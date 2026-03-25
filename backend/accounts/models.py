import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class SystemRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", _("Super Admin")
    ORG_ADMIN = "ORG_ADMIN", _("Org Admin")
    HO_USER = "HO_USER", _("HO User")
    RO_USER = "RO_USER", _("RO User")
    PIU_USER = "PIU_USER", _("PIU User")
    PROJECT_USER = "PROJECT_USER", _("Project User")
    CONTRACTOR = "CONTRACTOR", _("Contractor")

class UserManager(BaseUserManager):
    """
    Custom manager that uses email as the unique identifier
    instead of Django's default username field.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required."))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "SUPER_ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for the Road Management Platform.

    Key decisions:
    - UUID primary key (safe for public URLs, globally unique)
    - Email is the login identifier (username field removed / shadowed)
    - full_name replaces first_name + last_name for simplicity
    - phone is optional (useful for field engineers)

    AUTH_USER_MODEL = 'accounts.User' must be set in settings.py.
    Always set this BEFORE the first migration — it cannot be changed later
    without resetting the database.
    """

    # -------------------------------------------------------------------------
    # Override PK with UUID
    # -------------------------------------------------------------------------
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # -------------------------------------------------------------------------
    # Replace username with email
    # -------------------------------------------------------------------------
    username = None  # Remove the default username field
    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
        error_messages={
            "unique": _("A user with this email already exists."),
        },
    )

    # -------------------------------------------------------------------------
    # Profile fields
    # -------------------------------------------------------------------------
    full_name = models.CharField(
        _("full name"),
        max_length=255,
        blank=True,
    )
    phone = models.CharField(
        _("phone number"),
        max_length=20,
        blank=True,
    )
    
    # -------------------------------------------------------------------------
    # Multi-Organization Role-Based Access
    # -------------------------------------------------------------------------
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=SystemRole.choices,
        default=SystemRole.PROJECT_USER,
    )
    organization = models.ForeignKey(
        'orgs.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
        help_text=_("The organization this user belongs to. Null for Super Admins."),
    )
    ho_user = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinate_ho_users",
        help_text=_("The HO user this user reports to."),
    )
    ro_user = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinate_ro_users",
        help_text=_("The RO user this user reports to."),
    )
    piu_user = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinate_piu_users",
        help_text=_("The PIU user this user reports to."),
    )
    project_user = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinate_project_users",
        help_text=_("The Project user this user reports to."),
    )

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    # AbstractUser already provides date_joined; we add updated_at.
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------------------------------------------------------
    # Manager + auth config
    # -------------------------------------------------------------------------
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # createsuperuser will only ask for email + password

    class Meta:
        db_table = "accounts_user"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["email"]
        indexes = [
            models.Index(fields=["email"], name="idx_user_email"),
            models.Index(fields=["is_active"], name="idx_user_active"),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def display_name(self) -> str:
        """Returns full_name if set, otherwise the email prefix."""
        return self.full_name or self.email.split("@")[0]

    @property
    def is_platform_admin(self) -> bool:
        """
        Convenience property. True if this user has ANY UserOrgAccess
        record with role='admin'. Evaluated lazily — do not use in bulk loops.
        Import lazily to avoid circular imports.
        """
        from access.models import UserOrgAccess  # noqa: PLC0415
        return UserOrgAccess.objects.filter(
            user=self,
            role=UserOrgAccess.RoleChoices.ADMIN,
        ).exists()
