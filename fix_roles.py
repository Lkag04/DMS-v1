def fix_file(path, replacements):
    with open(path, "r") as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)


fix_file(
    "routers/transporter_router.py",
    [
        (
            'require_roles([ROLES["ADMIN"], ROLES["FACTORY"], ROLES["ACCOUNTS"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])',
        ),
        (
            'require_roles([ROLES["ADMIN"], ROLES["FACTORY"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])',
        ),
        (
            'require_roles([ROLES["ADMIN"], ROLES["ACCOUNTS"], ROLES["FACTORY"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])',
        ),
        (
            'require_roles([ROLES["ADMIN"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])',
        ),
    ],
)

fix_file(
    "routers/trip_router.py",
    [
        (
            'require_roles([ROLES["ADMIN"], ROLES["FACTORY"], ROLES["ACCOUNTS"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])',
        ),
        (
            'require_roles([ROLES["ADMIN"], ROLES["FACTORY"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])',
        ),
        (
            'require_roles([ROLES["ADMIN"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])',
        ),
    ],
)

fix_file(
    "routers/report_router.py",
    [
        (
            'require_roles([ROLES["ADMIN"], ROLES["ACCOUNTS"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["ADMIN"]])',
        )
    ],
)

fix_file(
    "routers/auth_router.py",
    [
        (
            'require_roles([ROLES["ADMIN"]])',
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["ADMIN"]])',
        )
    ],
)

print("Files fixed successfully.")
