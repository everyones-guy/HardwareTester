def log_routes(app):
    from logging import getLogger
    logger = getLogger(__name__)
    logger.info("=== URL MAP ===")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        logger.info("%s  ->  %s", ",".join(sorted(rule.methods)), rule.rule)

