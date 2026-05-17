from .models import Advertisement


def ads(request):
    return {
        'ads': {
            'hero': Advertisement.active_for_zone(Advertisement.HERO),
            'between_sections': Advertisement.active_for_zone(Advertisement.BETWEEN_SECTIONS),
            'vendor_list_top': Advertisement.active_for_zone(Advertisement.VENDOR_LIST_TOP),
            'vendor_detail': Advertisement.active_for_zone(Advertisement.VENDOR_DETAIL),
        }
    }
