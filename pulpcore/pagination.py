from urllib.parse import urlparse

from django.urls import Resolver404, resolve
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination

from pulpcore.app.experiments import run_experiment
from pulpcore.app.models import RepositoryVersion, RepositoryVersionContentDetails
from pulpcore.app.util import resolve_prn


class RepositoryVersionSummaryPagination(LimitOffsetPagination):
    """Use the persisted repository-version summary for unfiltered content counts."""

    def paginate_queryset(self, queryset, request, view=None):
        self._request = request
        return super().paginate_queryset(queryset, request, view)

    def _get_repository_version(self, href):
        if href.startswith("prn:"):
            model, version_pk = resolve_prn(href)
            if model is not RepositoryVersion:
                return None
            return RepositoryVersion.objects.get(
                pk=version_pk,
                repository__pulp_domain=self._request.pulp_domain,
            )

        try:
            href_kwargs = resolve(urlparse(href).path).kwargs
        except Resolver404:
            return None
        if "repository_pk" not in href_kwargs or "number" not in href_kwargs:
            return None
        return RepositoryVersion.objects.get(
            repository__pulp_id=href_kwargs["repository_pk"],
            number=int(href_kwargs["number"]),
            repository__pulp_domain=self._request.pulp_domain,
        )

    def get_count(self, queryset):
        version_filters = {
            "repository_version": "count",
            "repository_version_added": "added_count",
            "repository_version_removed": "removed_count",
        }
        selected_filters = [key for key in version_filters if key in self._request.query_params]
        if len(selected_filters) != 1:
            return super().get_count(queryset)
        version_filter = selected_filters[0]
        repository_version_href = self._request.query_params[version_filter]

        # A summary is exact for a completed, immutable repository version.  Only use it for
        # the unfiltered content query; arbitrary filters require the database count.
        if any(
            key not in {"repository_version", "limit", "offset", "ordering", "fields"}
            for key in self._request.query_params
        ):
            return super().get_count(queryset)

        try:
            version = self._get_repository_version(repository_version_href)
            if version is None or not version.complete:
                return super().get_count(queryset)
            pulp_type = queryset.model.get_pulp_type()
            count_type = {
                "repository_version": RepositoryVersionContentDetails.PRESENT,
                "repository_version_added": RepositoryVersionContentDetails.ADDED,
                "repository_version_removed": RepositoryVersionContentDetails.REMOVED,
            }[version_filter]
            if not version.counts.filter(count_type=count_type, content_type=pulp_type).exists():
                return super().get_count(queryset)

            return run_experiment(
                "PULP-1996-COUNT",
                control=queryset.count,
                candidate=lambda: getattr(version, version_filters[version_filter])(pulp_type),
                correlation_id=self._request.META.get("HTTP_CORRELATION_ID"),
            )
        except (RepositoryVersion.DoesNotExist, ValidationError, ValueError):
            return super().get_count(queryset)
