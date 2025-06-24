DELETE FROM auth_user
WHERE id IN (
    SELECT DISTINCT user_id
    FROM registration_registrationprofile
    WHERE activated = 0
);