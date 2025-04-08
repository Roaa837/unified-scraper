from scrapy.dupefilters import RFPDupeFilter
from urllib.parse import urlparse


class GRSRootPathAwareDupeFilter(RFPDupeFilter):
    def request_fingerprint(self, request):
        # Skip duplicate check for root path links (`/`)
        if urlparse(request.url).path == '/':
            return None  # Bypass duplicate filtering

        # Default behavior for other URLs
        return super().request_fingerprint(request)