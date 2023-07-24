FROM hibou/hibou-odoo:9.0

USER odoo
# Will NOT be able to run athen in Odoo 9  No need to copy it!
# COPY --from=registry.gitlab.com/hibou-io/athene:node12 /opt/athene /opt/athene
COPY --from=hibou/flow /flow /flow
COPY --chown=104 entrypoint.sh /entrypoint.sh
COPY --chown=104 . /opt/odoo/hibou-suite
RUN rm /etc/odoo/odoo.conf \
    && cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf \
    ;

EXPOSE 3000
ENV SHELL=/bin/bash \
    THEIA_DEFAULT_PLUGINS=local-dir:/opt/athene/plugins
ENV USE_LOCAL_GIT true

