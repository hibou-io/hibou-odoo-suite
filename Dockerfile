FROM hibou/hibou-odoo:20.0

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/supervisor \
    && mkdir -p /etc/supervisor/conf.d \
    && mkdir -p /etc/supervisor/override.d \
    && mkdir -p /opt/odoo-scripts \
    && rm -f /etc/supervisor/conf.d/* \
    ;
COPY docker/supervisord.conf /etc/supervisor/supervisord.conf
COPY docker/supervisor.d/odoo.conf /etc/supervisor/conf.d/odoo.conf
COPY docker/supervisor.d/athene.conf /etc/supervisor/conf.d/athene.conf
COPY docker/scripts/odoo-env.sh /opt/odoo-scripts/odoo-env.sh
COPY docker/scripts/odoo-server.sh /opt/odoo-scripts/odoo-server.sh
COPY docker/scripts/odoo-reload /usr/local/bin/odoo-reload
RUN chmod +x /opt/odoo-scripts/*.sh /usr/local/bin/odoo-reload \
    && chown -R 104 /opt/odoo-scripts /var/log/supervisor /etc/supervisor/override.d \
    ;

USER odoo
COPY --from=hibou/flow /flow /flow
COPY --chown=104 entrypoint.sh /entrypoint.sh
COPY --chown=104 . /opt/odoo/hibou-suite
RUN rm /etc/odoo/odoo.conf \
    && cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf \
    ;

EXPOSE 8069 8072 3000
