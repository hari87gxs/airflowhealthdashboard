{{/*
Expand the name of the chart.
*/}}
{{- define "airflow-health-dashboard.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "airflow-health-dashboard.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "airflow-health-dashboard.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "airflow-health-dashboard.labels" -}}
helm.sh/chart: {{ include "airflow-health-dashboard.chart" . }}
{{ include "airflow-health-dashboard.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "airflow-health-dashboard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "airflow-health-dashboard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "airflow-health-dashboard.backend.labels" -}}
{{ include "airflow-health-dashboard.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "airflow-health-dashboard.backend.selectorLabels" -}}
{{ include "airflow-health-dashboard.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "airflow-health-dashboard.frontend.labels" -}}
{{ include "airflow-health-dashboard.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "airflow-health-dashboard.frontend.selectorLabels" -}}
{{ include "airflow-health-dashboard.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Redis labels
*/}}
{{- define "airflow-health-dashboard.redis.labels" -}}
{{ include "airflow-health-dashboard.labels" . }}
app.kubernetes.io/component: redis
{{- end }}

{{/*
Redis selector labels
*/}}
{{- define "airflow-health-dashboard.redis.selectorLabels" -}}
{{ include "airflow-health-dashboard.selectorLabels" . }}
app.kubernetes.io/component: redis
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "airflow-health-dashboard.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "airflow-health-dashboard.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the image repository
*/}}
{{- define "airflow-health-dashboard.backend.image" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.backend.image.repository (.Values.backend.image.tag | default .Chart.AppVersion) }}
{{- else }}
{{- printf "%s:%s" .Values.backend.image.repository (.Values.backend.image.tag | default .Chart.AppVersion) }}
{{- end }}
{{- end }}

{{- define "airflow-health-dashboard.frontend.image" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.frontend.image.repository (.Values.frontend.image.tag | default .Chart.AppVersion) }}
{{- else }}
{{- printf "%s:%s" .Values.frontend.image.repository (.Values.frontend.image.tag | default .Chart.AppVersion) }}
{{- end }}
{{- end }}

{{- define "airflow-health-dashboard.redis.image" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.redis.image.repository .Values.redis.image.tag }}
{{- else }}
{{- printf "%s:%s" .Values.redis.image.repository .Values.redis.image.tag }}
{{- end }}
{{- end }}

{{/*
Get Redis URL
*/}}
{{- define "airflow-health-dashboard.redisUrl" -}}
{{- if .Values.redis.external.enabled }}
{{- .Values.redis.external.url }}
{{- else if .Values.redis.enabled }}
{{- printf "redis://%s-redis:%d" (include "airflow-health-dashboard.fullname" .) (.Values.redis.service.port | int) }}
{{- else }}
{{- "" }}
{{- end }}
{{- end }}
