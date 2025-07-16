{{- define "backup-jobs.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "backup-jobs.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if .Values.fullnameOverride -}}
{{- $name = .Values.fullnameOverride -}}
{{- end -}}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "backup-jobs.labels" -}}
helm.sh/chart: {{ include "backup-jobs.chart" . }}
{{ include "backup-jobs.selectorLabels" . }}
{{- if .Chart.AppVersion -}}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "backup-jobs.selectorLabels" -}}
app.kubernetes.io/name: {{ include "backup-jobs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "backup-jobs.chart" -}}
{{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}
