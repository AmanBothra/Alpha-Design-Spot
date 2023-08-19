from django.utils.translation import gettext_lazy as _

USER_TYPE = [
    ('admin', 'admin'),
    ('customer', 'customer')
]

FILE_TYPE = [
    ('image', 'image'),
    ('video', 'video')
]


class UserConstants:
    EMAIL_VERIFICATION, FORGOTTEN_PASSWORD, MOBILE_VERIFICATION = (
        "Email Verification",
        "Forgotten Password",
        "Mobile Verification",
    )

    @classmethod
    def get_code_type_choices(cls):
        CHOICES = [
            (cls.EMAIL_VERIFICATION, _("Email Verification")),
            (cls.FORGOTTEN_PASSWORD, _("Forgotten Password")),
            (cls.MOBILE_VERIFICATION, _("Mobile Verification")),
        ]
        return CHOICES