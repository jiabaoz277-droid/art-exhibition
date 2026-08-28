import { SubmissionWizard } from "./submission-wizard";

export default async function Page({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <SubmissionWizard token={token} />;
}
