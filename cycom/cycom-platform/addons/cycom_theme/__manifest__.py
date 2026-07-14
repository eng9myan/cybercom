{
    "name": "Cycom Theme",
    "summary": "Brand the Cycom backend as Cycom ERP — logos, colors, login screen, titles.",
    "version": "19.0.1.0.0",
    "category": "Theme/Backend",
    "author": "Cycom",
    "license": "LGPL-3",
    "depends": ["web", "base_setup"],
    "data": [
        "data/ir_config_parameter.xml",
        "views/login_templates.xml",
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cycom_theme/static/src/scss/cycom_variables.scss",
        ],
        "web.assets_frontend": [
            "cycom_theme/static/src/scss/cycom_variables.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
