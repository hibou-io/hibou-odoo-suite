FROM hibou/hibou-odoo:12.0

COPY . /opt/odoo/hibou-suite
RUN cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf

