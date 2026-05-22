import shortuuid
import qrcode
import io
import base64
from urllib.parse import urlencode, quote
from app.models import MarketplaceType, UTMMetadata, DiplinkResponse
from config import settings
from datetime import datetime


class DiplinkGenerator:
    """Generate deep links for different marketplaces"""

    @staticmethod
    def generate_short_code() -> str:
        """Generate a short code for the link"""
        return shortuuid.uuid()[:settings.SHORT_CODE_LENGTH]

    @staticmethod
    def generate_qr_code(url: str) -> str:
        """Generate QR code and return as base64 data URL"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            print(f"QR code generation error: {e}")
            return None

    @staticmethod
    def build_utm_string(utm: UTMMetadata, trax_id: str) -> str:
        """Build UTM query string"""
        params = {
            "trax_id": trax_id,
            "utm_source": utm.utm_source,
            "utm_medium": utm.utm_medium,
            "utm_campaign": utm.utm_campaign,
        }
        
        if utm.utm_term:
            params["utm_term"] = utm.utm_term
        if utm.utm_content:
            params["utm_content"] = utm.utm_content

        return urlencode(params)

    @staticmethod
    def generate_wildberries_deeplink(
        nm_id: str, utm_string: str
    ) -> dict:
        """
        Generate WB deeplinks for different platforms.
        
        Returns dict with keys: intent, ios, web
        """
        
        # Intent-based (Android)
        intent_link = f"intent://product-detail?nm_id={nm_id}&{utm_string}#Intent;scheme=wildberries;package=com.wildberries.ru;end"

        # iOS scheme
        ios_link = f"wildberries://product-detail?nm_id={nm_id}&{utm_string}"

        # Web fallback
        web_link = f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx?{utm_string}"

        return {
            "intent": intent_link,
            "ios": ios_link,
            "web": web_link,
            "primary": web_link,  # Default for short URLs
        }

    @staticmethod
    def generate_ozon_deeplink(
        product_id: str, utm_string: str
    ) -> dict:
        """
        Generate Ozon deeplinks.
        Prefer OneLink service for maximum compatibility.
        """

        # OneLink (recommended)
        onelink = f"https://ozon.ru/onelink/{product_id}/?{utm_string}"

        # Deeplink scheme
        deeplink = f"ozon://products/{product_id}/?{utm_string}"

        # Web fallback
        web_link = f"https://www.ozon.ru/product/{product_id}/?{utm_string}"

        return {
            "onelink": onelink,
            "deeplink": deeplink,
            "web": web_link,
            "primary": onelink,  # Default
        }

    @staticmethod
    def build_short_url(
        short_code: str, domain_name: str = None
    ) -> str:
        """Build short URL from short code and domain"""
        domain = domain_name or settings.SYSTEM_DOMAIN
        return f"https://{domain}/l/{short_code}"

    @staticmethod
    def generate_deeplink(
        marketplace: MarketplaceType,
        external_product_id: str,
        utm_metadata: UTMMetadata,
        trax_id: str,
        short_code: str,
        custom_domain: str = None,
    ) -> dict:
        """
        Main method to generate a complete deeplink package.
        
        Args:
            marketplace: Marketplace type (WB, Ozon)
            external_product_id: Product SKU/ID
            utm_metadata: UTM parameters
            trax_id: Unique tracking ID
            short_code: Generated short code
            custom_domain: Custom domain if available
            
        Returns:
            dict with deeplink_packages, short_url, full_url, qr_code
        """

        # Build UTM string
        utm_string = DiplinkGenerator.build_utm_string(utm_metadata, trax_id)

        # Generate marketplace-specific links
        if marketplace == MarketplaceType.WB:
            deeplink_packages = DiplinkGenerator.generate_wildberries_deeplink(
                external_product_id, utm_string
            )
        elif marketplace == MarketplaceType.OZON:
            deeplink_packages = DiplinkGenerator.generate_ozon_deeplink(
                external_product_id, utm_string
            )
        else:
            raise ValueError(f"Unknown marketplace: {marketplace}")

        # Build short URL
        short_url = DiplinkGenerator.build_short_url(short_code, custom_domain)

        # Generate QR code
        qr_code_url = DiplinkGenerator.generate_qr_code(short_url)

        # Full deeplink (primary for this marketplace)
        full_deeplink = deeplink_packages.get("primary", deeplink_packages.get("web"))

        return {
            "short_code": short_code,
            "short_url": short_url,
            "full_deeplink": full_deeplink,
            "deeplink_packages": deeplink_packages,
            "qr_code_url": qr_code_url,
        }

    @staticmethod
    def validate_external_product_id(external_product_id: str) -> bool:
        """
        Validate external product ID format.
        Should be numeric for both WB (nm_id) and Ozon.
        """
        try:
            int(external_product_id)
            return True
        except ValueError:
            return False
