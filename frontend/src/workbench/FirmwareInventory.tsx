import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { workspaceRequest } from './backend';

type Abi = { architecture: string; bits: number; endianness: string };
export type InventorySummary = { fileCount: number; elfAbis: Abi[]; unknownElfCount: number };

type Inventory = InventorySummary & {
  languages: string[];
  libc: string[];
  librariesNotBundled: string[];
  neededLibraries: string[];
  uiCatalogSha256: string | null;
  diagnostics: { path?: string; message: string }[];
  files: {
    path: string;
    sizeBytes: number;
    sha256: string;
    kind: string;
    confidence: string;
    format?: string;
    metadata?: Record<string, string | number>;
    elf?: {
      architecture: string | null;
      machine: number;
      type: string;
      osAbi: number;
      abiVersion: number;
      bits: number;
      endianness: string;
      interpreter: string | null;
      soname: string | null;
      needed: string[];
    };
  }[];
};

export default function FirmwareInventory({ digest }: { digest: string }) {
  const [inventory, setInventory] = useState<Inventory>();
  const [error, setError] = useState('');

  useEffect(() => {
    let current = true;
    void workspaceRequest<{ inventory: Inventory }>(`/firmware/${digest}/inventory`)
      .then((result) => {
        if (current) setInventory(result.inventory);
      })
      .catch((failure: Error) => {
        if (current) setError(failure.message);
      });
    return () => {
      current = false;
    };
  }, [digest]);

  if (error) return <p role="alert">{error}</p>;
  if (!inventory) return <p role="status">Reading saved inventory…</p>;
  return (
    <section className="firmware-inventory" aria-label="Release inventory">
      <dl>
        <dt>Languages</dt>
        <dd>{inventory.languages.join(', ') || 'Unidentified'}</dd>
        <dt>ELF architecture and ABI</dt>
        <dd>
          {inventory.elfAbis
            .map((abi) => `${abi.architecture} · ${abi.bits}-bit · ${abi.endianness}-endian`)
            .join('; ') || 'Unobserved'}
        </dd>
        <dt>Detected libc</dt>
        <dd>{inventory.libc.join(', ') || 'Unobserved'}</dd>
        <dt>Linked libraries</dt>
        <dd>{inventory.neededLibraries.join(', ') || 'None detected'}</dd>
        <dt>Linked libraries absent from this bundle</dt>
        <dd>{inventory.librariesNotBundled.join(', ') || 'None detected'}</dd>
      </dl>
      {inventory.uiCatalogSha256 && (
        <p>
          <NavLink to={`/ui-see?catalog=${inventory.uiCatalogSha256}`}>
            Open discovered UI catalog
          </NavLink>
        </p>
      )}
      {inventory.diagnostics.length > 0 && (
        <details>
          <summary>Inspection messages ({inventory.diagnostics.length})</summary>
          <ul>
            {inventory.diagnostics.map(({ path, message }, index) => (
              <li key={`${path}-${index}`}>
                {path && `${path} · `}
                {message}
              </li>
            ))}
          </ul>
        </details>
      )}
      <details open>
        <summary>Files ({inventory.fileCount})</summary>
        <ul className="firmware-inventory-files">
          {inventory.files.map((file) => (
            <li key={file.path}>
              <details>
                <summary>
                  <code>{file.path}</code> · {file.format ?? file.kind}
                </summary>
                <p>
                  {file.sizeBytes.toLocaleString()} bytes · Evidence from {file.confidence}
                </p>
                <p>
                  SHA-256 <code>{file.sha256}</code>
                </p>
                {file.metadata && (
                  <p>
                    {Object.entries(file.metadata)
                      .map(([key, value]) => `${key} ${value}`)
                      .join(' · ')}
                  </p>
                )}
                {file.elf && (
                  <p>
                    {file.elf.type} · Machine {file.elf.machine} · ABI {file.elf.osAbi}/
                    {file.elf.abiVersion}
                    {file.elf.interpreter && ` · Loader ${file.elf.interpreter}`}
                    {file.elf.soname && ` · SONAME ${file.elf.soname}`}
                    {file.elf.needed.length > 0 && ` · Needs ${file.elf.needed.join(', ')}`}
                  </p>
                )}
              </details>
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
