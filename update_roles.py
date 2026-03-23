import re

files = [
    "routers/report_router.py",
    "routers/trip_router.py",
    "routers/transporter_router.py",
    "routers/auth_router.py",
]

for filepath in files:
    with open(filepath, "r") as file:
        content = file.read()

    if "report_router" in filepath:
        content = re.sub(
            r"require_roles\s*\(\[[^\]]*\]\)",
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["ADMIN"]])',
            content,
        )
    elif "transporter_router" in filepath:
        content = re.sub(
            r"require_roles\s*\(\[[^\]]*\]\)",
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])',
            content,
        )
    elif "trip_router" in filepath:
        content = re.sub(
            r"require_roles\s*\(\[[^\]]*\]\)",
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])',
            content,
        )
    elif "auth_router" in filepath:
        content = re.sub(
            r"require_roles\s*\(\[[^\]]*\]\)",
            'require_roles([ROLES["MASTER_ADMIN"], ROLES["ADMIN"]])',
            content,
        )

    with open(filepath, "w") as file:
        file.write(content)

print("Roles updated successfully in python routers.")
