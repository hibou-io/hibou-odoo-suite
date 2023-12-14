FROM hibou/hibou-odoo:11.0

USER odoo
COPY --from=hibou/flow /flow /flow
COPY --chown=104 entrypoint.sh /entrypoint.sh
COPY --chown=104 . /opt/odoo/hibou-suite
RUN rm /etc/odoo/odoo.conf \
    && cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf \
    ;

USER 0
RUN cd /opt/odoo/hibou-suite/external/python-amazon-sp-api \
  && pip install .
USER 104

