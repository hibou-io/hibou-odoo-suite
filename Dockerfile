FROM hibou/hibou-odoo:14.0

USER 104
COPY --from=hibou/flow /flow /flow
COPY --chown=104 entrypoint.sh /entrypoint.sh
COPY --chown=104 . /opt/odoo/hibou-suite
RUN rm /etc/odoo/odoo.conf \
    && cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf \
    ;

EXPOSE 3000
ENV SHELL=/bin/bash \
    THEIA_DEFAULT_PLUGINS=local-dir:/opt/theia/plugins
ENV USE_LOCAL_GIT true

