import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Sans « globals » dans la config, Testing Library ne démonte pas les rendus tout seul :
// chaque test doit repartir d'un document vide.
afterEach(() => cleanup());
