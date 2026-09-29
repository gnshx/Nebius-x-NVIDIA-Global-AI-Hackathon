import { Settings, Github, Server, Key, ExternalLink } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface InfoRowProps {
  label: string;
  value: string;
  mono?: boolean;
}

function InfoRow({ label, value, mono = false }: InfoRowProps) {
  return (
    <div className="flex items-start justify-between gap-4 py-3 border-b last:border-0">
      <span className="text-sm text-muted-foreground shrink-0">{label}</span>
      <span className={`text-sm text-right break-all ${mono ? 'font-mono text-xs bg-muted px-2 py-0.5 rounded' : 'font-medium'}`}>
        {value}
      </span>
    </div>
  );
}

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function Section({ title, icon, children }: SectionProps) {
  return (
    <div className="rounded-xl border bg-card overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-4 border-b bg-muted/20">
        {icon}
        <h2 className="text-base font-semibold">{title}</h2>
      </div>
      <div className="px-5">{children}</div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Environment configuration and setup instructions
        </p>
      </div>

      {/* API Configuration */}
      <Section title="API Configuration" icon={<Server className="h-5 w-5 text-muted-foreground" />}>
        <InfoRow label="API URL" value={API_URL} mono />
        <InfoRow label="Environment" value={process.env.NODE_ENV ?? 'development'} />
        <InfoRow label="Frontend Version" value="0.1.0" />
      </Section>

      {/* Model Configuration */}
      <Section title="Model Configuration" icon={<Key className="h-5 w-5 text-muted-foreground" />}>
        <InfoRow
          label="Reasoning Model"
          value={process.env.REASONING_MODEL ?? 'nvidia/llama-3.1-nemotron-ultra-253b-v1'}
          mono
        />
        <InfoRow
          label="Fast Model"
          value={process.env.FAST_MODEL ?? 'meta/llama-3.3-70b-instruct'}
          mono
        />
        <InfoRow
          label="Embedding Model"
          value={process.env.EMBEDDING_MODEL ?? 'nvidia/llama-3.2-nv-embedqa-1b-v2'}
          mono
        />
        <InfoRow
          label="Provider"
          value="Nebius AI (NVIDIA NIM)"
        />
      </Section>

      {/* GitHub App Setup */}
      <Section
        title="GitHub App Setup"
        icon={<Github className="h-5 w-5 text-muted-foreground" />}
      >
        <div className="py-4 space-y-4 text-sm text-muted-foreground">
          <p>
            RepoMedic operates as a GitHub App. Follow these steps to configure the webhook:
          </p>
          <ol className="list-decimal list-inside space-y-2 text-foreground">
            <li>
              Create a GitHub App at{' '}
              <a
                href="https://github.com/settings/apps/new"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline-offset-2 underline inline-flex items-center gap-0.5"
              >
                github.com/settings/apps
                <ExternalLink className="h-3 w-3" />
              </a>
            </li>
            <li>
              Set the <strong>Webhook URL</strong> to{' '}
              <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                {API_URL}/api/webhook/github
              </code>
            </li>
            <li>
              Generate a <strong>Webhook Secret</strong> and set{' '}
              <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                GITHUB_WEBHOOK_SECRET
              </code>{' '}
              in the backend&apos;s <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">.env</code>
            </li>
            <li>
              Enable permissions: <strong>Issues (read)</strong>,{' '}
              <strong>Pull Requests (write)</strong>, <strong>Contents (write)</strong>
            </li>
            <li>
              Subscribe to events: <strong>Issues</strong>, <strong>Issue comment</strong>
            </li>
            <li>
              Install the app on your target repositories and register them in the{' '}
              <strong>Repositories</strong> tab.
            </li>
          </ol>
          <p className="text-xs mt-2">
            See the{' '}
            <a
              href="https://github.com/gojo/repomedic"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline-offset-2 underline inline-flex items-center gap-0.5"
            >
              RepoMedic README
              <ExternalLink className="h-3 w-3" />
            </a>{' '}
            for full setup instructions.
          </p>
        </div>
      </Section>
    </div>
  );
}
