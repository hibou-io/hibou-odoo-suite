FROM hibou/hibou-odoo:16.0

USER odoo
COPY --from=hibou/flow /flow /flow
COPY --chown=104 entrypoint.sh /entrypoint.sh
COPY --chown=104 . /opt/odoo/hibou-suite
RUN rm /etc/odoo/odoo.conf \
    && cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf \
    ;

