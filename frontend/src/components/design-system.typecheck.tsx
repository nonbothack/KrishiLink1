import {
  Badge,
  Button,
  Card,
  DataState,
  Field,
  Notice,
  PageHeading,
  StatusPill,
} from './Experience';

export const designSystemTypeContract = (
  <>
    <PageHeading title="Market prices" description="Choose a crop and market." />
    <Card as="article" variant="emphasized" aria-label="Latest price">
      <Badge tone="success">Reported today</Badge>
      <StatusPill tone="warning">Price may be stale</StatusPill>
      <Field label="Crop" as="select" autoComplete="off">
        <option value="wheat">Wheat</option>
      </Field>
      <Button type="submit" variant="primary" size="large" loading>
        Check price
      </Button>
      <Notice error>Could not load current prices.</Notice>
    </Card>
    <DataState loading />
  </>
);
