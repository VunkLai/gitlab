# URLs
external_url 'https://gitlab.example.com'

# SSL
letsencrypt['enable'] = true
letsencrypt['contact_emails'] = ['user-name@gmail.com']
letsencrypt['auto_renew'] = true
letsencrypt['auto_renew_day_of_month'] = "*/7"

# Registry
registry['enable'] = false

# Puma
puma['exporter_enabled'] = true
puma['exporter_port'] = 8083

# sidekiq
sidekiq['metrics_enabled'] = true
sidekiq['listen_port'] = 8082

# Prometheus
prometheus['enable'] = true
prometheus['listen_address'] = 'localhost:9090'

# Grafana
grafana['enable'] = false

# Exporters
node_exporter['enable'] = true
node_exporter['listen_address'] = 'localhost:9100'

redis_exporter['enable'] = true
redis_exporter['listen_address'] = 'localhost:9121'

postgres_exporter['enable'] = true
postgres_exporter['listen_address'] = 'localhost:9187'

gitlab_exporter['enable'] = true
gitlab_exporter['listen_address'] = 'localhost'
gitlab_exporter['listen_port'] = '9168'
