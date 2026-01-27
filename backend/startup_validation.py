def validate_startup_plan(plan: dict):
    # ---------- Basic structure ----------
    required_top = ["version", "database", "paths", "layout", "options", "review"]
    for k in required_top:
        if k not in plan:
            raise ValueError(f"PLAN_MISSING_FIELD:{k}")

    # ---------- Database ----------
    db = plan["database"]
    if not db.get("db_path"):
        raise ValueError("DB_PATH_MISSING")

    if db.get("mode") not in ("new", "existing"):
        raise ValueError("INVALID_DB_MODE")

    # ---------- Paths ----------
    paths = plan["paths"]

    if not paths.get("source"):
        raise ValueError("SOURCE_PATH_MISSING")

    if not paths.get("target"):
        raise ValueError("TARGET_PATH_MISSING")

    # Enforce your invariant:
    # If imported DB, source must be locked
    if paths.get("locked_by_database") is True:
        # source must not be empty and must not be changed later
        pass  # nothing to enforce here yet, but hook is ready

    # ---------- Review ----------
    review = plan["review"]
    if not review.get("confirmed"):
        raise ValueError("REVIEW_NOT_CONFIRMED")

    # ---------- Options ----------
    opts = plan["options"]

    # Default missing flags safely
    opts.setdefault("with_fingerprint", False)
    opts.setdefault("search_covers", False)
    opts.setdefault("dry_run", True)
    opts.setdefault("no_overwrite", True)

    return True
