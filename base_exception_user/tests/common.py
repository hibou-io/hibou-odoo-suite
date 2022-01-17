# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2020 Hibou Corp.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def setup_test_model(env, model_clses):
    model_names = set()
    for model_cls in model_clses:
        model = model_cls._build_model(env.registry, env.cr)
        model_names.add(model._name)

    env.registry.setup_models(env.cr)
    env.registry.init_models(
        env.cr,
        model_names,
        dict(env.context, update_custom_fields=True),
    )
