import base64
import hmac
import json
import secrets
import struct
from operator import mul

import pyotp
import webauthn
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Max, Q, UniqueConstraint
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from fernet_fields import EncryptedCharField
from pyotp.utils import strings_equal
from sortedm2m.fields import SortedManyToManyField

from judge.models.choices import ACE_THEMES, MATH_ENGINES_CHOICES, SITE_THEMES, TIMEZONE
from judge.models.runtime import Language
from judge.ratings import rating_class
from judge.utils.two_factor import webauthn_decode

__all__ = ['Class', 'Organization', 'Profile', 'OrganizationRequest', 'WebAuthnCredential']


class EncryptedNullCharField(EncryptedCharField):
    def get_prep_value(self, value):
        if not value:
            return None
        return super(EncryptedNullCharField, self).get_prep_value(value)


class Organization(models.Model):
    name = models.CharField(max_length=128, verbose_name=_('organization title'))
    slug = models.SlugField(max_length=128, verbose_name=_('organization slug'),
                            help_text=_('Organization name shown in URLs.'))
    short_name = models.CharField(max_length=20, verbose_name=_('short name'),
                                  help_text=_('Displayed beside user name during contests.'))
    about = models.TextField(verbose_name=_('organization description'))
    admins = models.ManyToManyField('Profile', verbose_name=_('administrators'), related_name='admin_of',
                                    help_text=_('Those who can edit this organization.'))
    creation_date = models.DateTimeField(verbose_name=_('creation date'), auto_now_add=True)
    is_open = models.BooleanField(verbose_name=_('is open organization?'),
                                  help_text=_('Allow joining organization.'), default=True)
    slots = models.IntegerField(verbose_name=_('maximum size'), null=True, blank=True,
                                help_text=_('Maximum amount of users in this organization, '
                                            'only applicable to private organizations.'))
    access_code = models.CharField(max_length=7, help_text=_('Student access code.'),
                                   verbose_name=_('access code'), null=True, blank=True)
    logo_override_image = models.CharField(verbose_name=_('logo override image'), default='', max_length=150,
                                           blank=True,
                                           help_text=_('This image will replace the default site logo for users '
                                                       'viewing the organization.'))
    class_required = models.BooleanField(verbose_name=_('class membership required'), default=False,
                                         help_text=_('Whether members are compelled to select a class when joining.'))

    def clean(self):
        if self.class_required and self.is_open:
            raise ValidationError(_('Class membership cannot be enforced when organization has open enrollment.'))

    def __contains__(self, item):
        if isinstance(item, int):
            return self.members.filter(id=item).exists()
        elif isinstance(item, Profile):
            return self.members.filter(id=item.id).exists()
        else:
            raise TypeError('Organization membership test must be Profile or primary key.')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization_home', args=(self.id, self.slug))

    def get_users_url(self):
        return reverse('organization_users', args=(self.id, self.slug))

    def can_review_all_requests(self, profile):
        return self.admins.filter(id=profile.id).exists()

    def can_review_class_requests(self, profile):
        return self.classes.filter(admins__id=profile.id).exists()

    class Meta:
        ordering = ['name']
        permissions = (
            ('organization_admin', _('Administer organizations')),
            ('edit_all_organization', _('Edit all organizations')),
        )
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')


class Class(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name=_('organization'),
                                     help_text=_('The organization that this class belongs to.'),
                                     related_name='classes', related_query_name='class')
    name = models.CharField(max_length=128, verbose_name=_('class name'), unique=True)
    slug = models.SlugField(max_length=128, verbose_name=_('class slug'), help_text=_('Class name shown in URLs.'))
    description = models.TextField(verbose_name=_('class description'), blank=True)
    is_active = models.BooleanField(verbose_name=_('is class active'), default=True)
    access_code = models.CharField(max_length=7, verbose_name=_('access code'), null=True, blank=True,
                                   help_text=_('Student access code.'))
    admins = models.ManyToManyField('Profile', verbose_name=_('administrators'), related_name='class_admin_of',
                                    help_text=_('Those who can approve membership to this class.'))
    members = models.ManyToManyField('Profile', verbose_name=_('members'), blank=True,
                                     related_name='classes', related_query_name='class')

    @classmethod
    def get_visible_classes(cls, user):
        if not user.is_authenticated:
            return cls.objects.none()

        if user.has_perm('judge.edit_all_organization'):
            return cls.objects.all()

        return cls.objects.filter(contest__organizations__admins=user.profile) | cls.objects.filter(admins=user.profile)

    def __str__(self):
        return _('%(class)s in %(organization)s') % {'class': self.name, 'organization': self.organization.name}

    def get_absolute_url(self):
        return reverse('class_home', args=self._url_args)

    def get_join_url(self):
        return reverse('class_join', args=self._url_args)

    @cached_property
    def _url_args(self):
        return self.organization.id, self.organization.slug, self.id, self.slug

    class Meta:
        ordering = ['organization', 'name']
        verbose_name = _('class')
        verbose_name_plural = _('classes')
        constraints = [UniqueConstraint(fields=['name'], condition=Q(is_active=True), name='unique_active_name')]


class Profile(models.Model):
    user = models.OneToOneField(User, verbose_name=_('user associated'), on_delete=models.CASCADE)
    about = models.TextField(verbose_name=_('self-description'), null=True, blank=True)
    timezone = models.CharField(max_length=50, verbose_name=_('time zone'), choices=TIMEZONE,
                                default=settings.DEFAULT_USER_TIME_ZONE)
    language = models.ForeignKey('Language', verbose_name=_('preferred language'), on_delete=models.SET_DEFAULT,
                                 default=Language.get_default_language_pk)
    points = models.FloatField(default=0)
    performance_points = models.FloatField(default=0)
    problem_count = models.IntegerField(default=0)
    ace_theme = models.CharField(max_length=30, verbose_name=_('Ace theme'), choices=ACE_THEMES, default='auto')
    site_theme = models.CharField(max_length=10, verbose_name=_('site theme'), choices=SITE_THEMES, default='auto')
    last_access = models.DateTimeField(verbose_name=_('last access time'), default=now)
    ip = models.GenericIPAddressField(verbose_name=_('last IP'), blank=True, null=True)
    organizations = SortedManyToManyField(Organization, verbose_name=_('organization'), blank=True,
                                          related_name='members', related_query_name='member')
    display_rank = models.CharField(max_length=10, default='user', verbose_name=_('display rank'),
                                    choices=(
                                        ('user', _('Normal User')),
                                        ('setter', _('Problem Setter')),
                                        ('admin', _('Admin'))))
    mute = models.BooleanField(verbose_name=_('comment mute'), help_text=_('Some users are at their best when silent.'),
                               default=False)
    is_unlisted = models.BooleanField(verbose_name=_('unlisted user'), help_text=_('User will not be ranked.'),
                                      default=False)
    is_banned_from_problem_voting = models.BooleanField(
        verbose_name=_('banned from voting on problem point values'),
        help_text=_("User will not be able to vote on problems' point values."),
        default=False,
    )
    rating = models.IntegerField(null=True, default=None)
    user_script = models.TextField(verbose_name=_('user script'), default='', blank=True, max_length=65536,
                                   help_text=_('User-defined JavaScript for site customization.'))
    current_contest = models.OneToOneField('ContestParticipation', verbose_name=_('current contest'),
                                           null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    math_engine = models.CharField(verbose_name=_('math engine'), choices=MATH_ENGINES_CHOICES, max_length=4,
                                   default=settings.MATHOID_DEFAULT_TYPE,
                                   help_text=_('The rendering engine used to render math.'))
    is_totp_enabled = models.BooleanField(verbose_name=_('TOTP 2FA enabled'), default=False,
                                          help_text=_('Check to enable TOTP-based two-factor authentication.'))
    is_webauthn_enabled = models.BooleanField(verbose_name=_('WebAuthn 2FA enabled'), default=False,
                                              help_text=_('Check to enable WebAuthn-based two-factor authentication.'))
    totp_key = EncryptedNullCharField(max_length=32, null=True, blank=True, verbose_name=_('TOTP key'),
                                      help_text=_('32-character Base32-encoded key for TOTP.'),
                                      validators=[RegexValidator('^$|^[A-Z2-7]{32}$',
                                                                 _('TOTP key must be empty or Base32.'))])
    scratch_codes = EncryptedNullCharField(max_length=255, null=True, blank=True, verbose_name=_('scratch codes'),
                                           help_text=_('JSON array of 16-character Base32-encoded codes '
                                                       'for scratch codes.'),
                                           validators=[
                                               RegexValidator(r'^(\[\])?$|^\[("[A-Z0-9]{16}", *)*"[A-Z0-9]{16}"\]$',
                                                              _('Scratch codes must be empty or a JSON array of '
                                                                '16-character Base32 codes.'))])
    last_totp_timecode = models.IntegerField(verbose_name=_('last TOTP timecode'), default=0)
    notes = models.TextField(verbose_name=_('internal notes'), null=True, blank=True,
                             help_text=_('Notes for administrators regarding this user.'))
    data_last_downloaded = models.DateTimeField(verbose_name=_('last data download time'), null=True, blank=True)
    username_display_override = models.CharField(max_length=100, blank=True, verbose_name=_('display name override'),
                                                 help_text=_('Name displayed in place of username.'))

    @cached_property
    def organization(self):
        # We do this to take advantage of prefetch_related
        orgs = self.organizations.all()
        return orgs[0] if orgs else None

    @cached_property
    def username(self):
        return self.user.username

    @cached_property
    def display_name(self):
        return self.username_display_override or self.username

    @cached_property
    def has_any_solves(self):
        return self.submission_set.filter(result='AC', case_points__gte=F('case_total')).exists()

    @cached_property
    def resolved_ace_theme(self):
        if self.ace_theme != 'auto':
            return self.ace_theme
        if not self.user.has_perm('judge.test_site'):
            return settings.DMOJ_THEME_DEFAULT_ACE_THEME.get('light')
        if self.site_theme != 'auto':
            return settings.DMOJ_THEME_DEFAULT_ACE_THEME.get(self.site_theme)
        # This must be resolved client-side using prefers-color-scheme.
        return None

    _pp_table = [pow(settings.DMOJ_PP_STEP, i) for i in range(settings.DMOJ_PP_ENTRIES)]

    def calculate_points(self, table=_pp_table):
        from judge.models import Problem
        public_problems = Problem.get_public_problems()
        data = (
            public_problems.filter(submission__user=self, submission__points__isnull=False)
                           .annotate(max_points=Max('submission__points')).order_by('-max_points')
                           .values_list('max_points', flat=True).filter(max_points__gt=0)
        )
        bonus_function = settings.DMOJ_PP_BONUS_FUNCTION
        points = sum(data)
        entries = min(len(data), len(table))
        problems = (
            public_problems.filter(submission__user=self, submission__result='AC',
                                   submission__case_points__gte=F('submission__case_total'))
            .values('id').distinct().count()
        )
        pp = sum(map(mul, table[:entries], data[:entries])) + bonus_function(problems)
        if self.points != points or problems != self.problem_count or self.performance_points != pp:
            self.points = points
            self.problem_count = problems
            self.performance_points = pp
            self.save(update_fields=['points', 'problem_count', 'performance_points'])
        return points

    calculate_points.alters_data = True

    def generate_scratch_codes(self):
        def generate_scratch_code():
            return ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567') for _ in range(16))
        codes = [generate_scratch_code() for _ in range(settings.DMOJ_SCRATCH_CODES_COUNT)]
        self.scratch_codes = json.dumps(codes)
        self.save(update_fields=['scratch_codes'])
        return codes

    generate_scratch_codes.alters_data = True

    def remove_contest(self):
        self.current_contest = None
        self.save()

    remove_contest.alters_data = True

    def update_contest(self):
        contest = self.current_contest
        if contest is not None and (contest.ended or not contest.contest.is_accessible_by(self.user)):
            self.remove_contest()

    update_contest.alters_data = True

    def check_totp_code(self, code):
        totp = pyotp.TOTP(self.totp_key)
        now_timecode = totp.timecode(timezone.now())
        min_timecode = max(self.last_totp_timecode + 1, now_timecode - settings.DMOJ_TOTP_TOLERANCE_HALF_MINUTES)
        for timecode in range(min_timecode, now_timecode + settings.DMOJ_TOTP_TOLERANCE_HALF_MINUTES + 1):
            if strings_equal(code, totp.generate_otp(timecode)):
                self.last_totp_timecode = timecode
                self.save(update_fields=['last_totp_timecode'])
                return True
        return False

    check_totp_code.alters_data = True

    def get_absolute_url(self):
        return reverse('user_page', args=(self.user.username,))

    def __str__(self):
        return self.user.username

    @classmethod
    def get_user_css_class(cls, display_rank, rating, rating_colors=settings.DMOJ_RATING_COLORS):
        if rating_colors:
            return 'rating %s %s' % (rating_class(rating) if rating is not None else 'rate-none', display_rank)
        return display_rank

    @cached_property
    def css_class(self):
        return self.get_user_css_class(self.display_rank, self.rating)

    @cached_property
    def webauthn_id(self):
        return hmac.new(force_bytes(settings.SECRET_KEY), msg=b'webauthn:%d' % (self.id,), digestmod='sha256').digest()

    class Meta:
        permissions = (
            ('test_site', _('Shows in-progress development stuff')),
            ('totp', _('Edit TOTP settings')),
        )
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

        indexes = [
            models.Index(fields=('is_unlisted', '-performance_points')),
            models.Index(fields=('is_unlisted', '-rating')),
            models.Index(fields=('is_unlisted', '-problem_count')),
        ]


class WebAuthnCredential(models.Model):
    user = models.ForeignKey(Profile, verbose_name=_('user'), related_name='webauthn_credentials',
                             on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_('device name'), max_length=100)
    cred_id = models.CharField(verbose_name=_('credential ID'), max_length=255, unique=True)
    public_key = models.TextField(verbose_name=_('public key'))
    counter = models.BigIntegerField(verbose_name=_('sign counter'))

    @cached_property
    def webauthn_user(self):
        from judge.jinja2.gravatar import gravatar

        return webauthn.WebAuthnUser(
            user_id=self.user.webauthn_id,
            username=self.user.username,
            display_name=self.user.username,
            icon_url=gravatar(self.user.user.email),
            credential_id=webauthn_decode(self.cred_id),
            public_key=self.public_key,
            sign_count=self.counter,
            rp_id=settings.WEBAUTHN_RP_ID,
        )

    def __str__(self):
        return _('WebAuthn credential: %(name)s') % {'name': self.name}

    class Meta:
        verbose_name = _('WebAuthn credential')
        verbose_name_plural = _('WebAuthn credentials')


class OrganizationRequest(models.Model):
    user = models.ForeignKey(Profile, verbose_name=_('user'), related_name='requests', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, verbose_name=_('organization'), related_name='requests',
                                     on_delete=models.CASCADE)
    time = models.DateTimeField(verbose_name=_('request time'), auto_now_add=True)
    state = models.CharField(max_length=1, verbose_name=_('state'), choices=(
        ('P', _('Pending')),
        ('A', _('Approved')),
        ('R', _('Rejected')),
    ))
    request_class = models.ForeignKey(Class, verbose_name=_('class'), on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField(verbose_name=_('reason'))

    def clean(self):
        if self.organization.class_required and self.request_class is None:
            raise ValidationError('Organization requires a class to be specified')
        if self.request_class and self.organization_id != self.request_class.organization_id:
            raise ValidationError('Class must be part of the organization')

    class Meta:
        verbose_name = _('organization join request')
        verbose_name_plural = _('organization join requests')
