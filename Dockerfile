FROM hibou/hibou-odoo:15.0

USER 0
COPY --from=registry.gitlab.com/hibou-io/theia-python /opt/theia /opt/theia
RUN set -x; \
        curl -sL https://deb.nodesource.com/setup_12.x | bash - \
        && apt-get install -y \
           nodejs \
           build-essential \
           libsecret-1-0 \
           procps \
        && npm install --global yarn

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

