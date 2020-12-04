FROM hibou/hibou-odoo:12.0

# All this just for openupgradelib
USER 0
RUN set -x; \
    apt update && apt install -y git \
    && pip install git+git://github.com/OCA/openupgradelib.git \
    # Clean Up
    && apt remove -y git \
    && apt autoremove -y \
    && rm -rf /root/.cache \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    ;

USER 104
COPY --from=hibou/flow /flow /flow
COPY --chown=104 entrypoint.sh /entrypoint.sh
COPY --chown=104 . /opt/odoo/hibou-suite
RUN rm /etc/odoo/odoo.conf \
    && cp /opt/odoo/hibou-suite/debian/odoo.conf /etc/odoo/odoo.conf \
    ;

