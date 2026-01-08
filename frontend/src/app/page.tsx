export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          CelesteOS OneDrive Integration
        </h1>
        <p className="text-center text-muted-foreground mb-12">
          Cloud-to-cloud document ingestion from OneDrive for Business
        </p>

        <div className="bg-card border rounded-lg p-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">Get Started</h2>
          <p className="text-muted-foreground mb-6">
            Connect your OneDrive account to start syncing documents to CelesteOS
          </p>

          <a
            href="/dashboard"
            className="inline-block bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-3 rounded-md font-medium"
          >
            Go to Dashboard
          </a>

          <p className="text-xs text-muted-foreground mt-6">
            Week 2: OAuth flow implemented ✅
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border rounded-lg p-6">
            <h3 className="font-semibold mb-2">1. Connect</h3>
            <p className="text-sm text-muted-foreground">
              Authorize CelesteOS to access your OneDrive for Business files
            </p>
          </div>

          <div className="border rounded-lg p-6">
            <h3 className="font-semibold mb-2">2. Browse</h3>
            <p className="text-sm text-muted-foreground">
              Select folders containing yacht documentation and manuals
            </p>
          </div>

          <div className="border rounded-lg p-6">
            <h3 className="font-semibold mb-2">3. Sync</h3>
            <p className="text-sm text-muted-foreground">
              Automatically process and index all your documents
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
