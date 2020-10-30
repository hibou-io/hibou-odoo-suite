FROM hibou/hibou-odoo:12.0

USER 0
RUN pip install git+git://github.com/OCA/openupgradelib.git

USER 104
COPY --chown=104 . /opt/odoo/hibou-suite
RUN rm /etc/odoo/odoo.conf \
    && cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf \
    ;

