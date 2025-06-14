from django.db import migrations

SQL_STATEMENTS = [
    # token_blacklist_outstandingtoken
    """
    ALTER TABLE token_blacklist_outstandingtoken
      DROP FOREIGN KEY token_blacklist_outs_user_id_83bc629a_fk_auth_user;
    """,
    """
    ALTER TABLE token_blacklist_outstandingtoken
      ADD CONSTRAINT token_blacklist_outs_user_id_83bc629a_fk_auth_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # auth_user_user_permissions
    """
    ALTER TABLE auth_user_user_permissions
      DROP FOREIGN KEY auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id;
    """,
    """
    ALTER TABLE auth_user_user_permissions
      ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # impersonate_impersonationlog – impersonating_id
    """
    ALTER TABLE impersonate_impersonationlog
      DROP FOREIGN KEY impersonate_imperson_impersonating_id_afd114fc_fk_auth_user;
    """,
    """
    ALTER TABLE impersonate_impersonationlog
      ADD CONSTRAINT impersonate_imperson_impersonating_id_afd114fc_fk_auth_user
        FOREIGN KEY (impersonating_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # impersonate_impersonationlog – impersonator_id
    """
    ALTER TABLE impersonate_impersonationlog
      DROP FOREIGN KEY impersonate_imperson_impersonator_id_1ecfe8ce_fk_auth_user;
    """,
    """
    ALTER TABLE impersonate_impersonationlog
      ADD CONSTRAINT impersonate_imperson_impersonator_id_1ecfe8ce_fk_auth_user
        FOREIGN KEY (impersonator_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # social_auth_usersocialauth
    """
    ALTER TABLE social_auth_usersocialauth
      DROP FOREIGN KEY social_auth_usersocialauth_user_id_17d28448_fk_auth_user_id;
    """,
    """
    ALTER TABLE social_auth_usersocialauth
      ADD CONSTRAINT social_auth_usersocialauth_user_id_17d28448_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # judge_profile
    """
    ALTER TABLE judge_profile
      DROP FOREIGN KEY judge_profile_user_id_b62d6977_fk_auth_user_id;
    """,
    """
    ALTER TABLE judge_profile
      ADD CONSTRAINT judge_profile_user_id_b62d6977_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # judge_contestfollow
    """
    ALTER TABLE judge_contestfollow
      DROP FOREIGN KEY judge_contestfollow_user_id_4a54cf4c_fk_auth_user_id;
    """,
    """
    ALTER TABLE judge_contestfollow
      ADD CONSTRAINT judge_contestfollow_user_id_4a54cf4c_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # reversion_revision
    """
    ALTER TABLE reversion_revision
      DROP FOREIGN KEY reversion_revision_user_id_17095f45_fk_auth_user_id;
    """,
    """
    ALTER TABLE reversion_revision
      ADD CONSTRAINT reversion_revision_user_id_17095f45_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # django_admin_log
    """
    ALTER TABLE django_admin_log
      DROP FOREIGN KEY django_admin_log_user_id_c564eba6_fk_auth_user_id;
    """,
    """
    ALTER TABLE django_admin_log
      ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # judge_blogpost_subscribers
    """
    ALTER TABLE judge_blogpost_subscribers
      DROP FOREIGN KEY judge_blogpost_subscribers_user_id_0672ff91_fk_auth_user_id;
    """,
    """
    ALTER TABLE judge_blogpost_subscribers
      ADD CONSTRAINT judge_blogpost_subscribers_user_id_0672ff91_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # registration_registrationprofile
    """
    ALTER TABLE registration_registrationprofile
      DROP FOREIGN KEY registration_registr_user_id_5fcbf725_fk_auth_user;
    """,
    """
    ALTER TABLE registration_registrationprofile
      ADD CONSTRAINT registration_registr_user_id_5fcbf725_fk_auth_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,

    # auth_user_groups
    """
    ALTER TABLE auth_user_groups
      DROP FOREIGN KEY auth_user_groups_user_id_6a12ed8b_fk_auth_user_id;
    """,
    """
    ALTER TABLE auth_user_groups
      ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
    """,
]

class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0165_contestfollow'),  # adjust if necessary
    ]

    operations = [
        migrations.RunSQL(sql=SQL_STATEMENTS, reverse_sql=migrations.RunSQL.noop),
    ]