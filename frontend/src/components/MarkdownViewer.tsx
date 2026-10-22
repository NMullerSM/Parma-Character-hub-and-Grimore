import React from "react";

interface MarkdownViewerProps {
  content: string;
  className?: string;
}

function renderInline(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-main">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return (
        <em key={i} className="italic text-gold/90">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          className="px-1.5 py-0.5 rounded bg-surface border border-border-iron font-stat text-[11px] text-gold"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export const MarkdownViewer: React.FC<MarkdownViewerProps> = ({ content, className = "" }) => {
  if (!content) return null;

  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i++;
      continue;
    }

    // Tablas Markdown (robusto para tablas con o sin barra final)
    if (trimmed.startsWith("|") && (trimmed.endsWith("|") || trimmed.includes("|"))) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }
      if (tableLines.length >= 2) {
        const parseRow = (rowStr: string): string[] => {
          let s = rowStr.trim();
          if (s.startsWith("|")) s = s.slice(1);
          if (s.endsWith("|")) s = s.slice(0, -1);
          return s.split("|").map((c) => c.trim());
        };

        const rawHeaders = parseRow(tableLines[0]);
        // Ignorar fila separadora tipo |---|---|
        const dataLines = tableLines
          .slice(1)
          .filter((r) => !/^\|?[\s:-]+(?:\|[\s:-]+)*\|?$/.test(r));

        const maxCols = Math.max(
          rawHeaders.length,
          ...dataLines.map((r) => parseRow(r).length)
        );

        // Rellenar cabeceras si faltan
        const headers = [...rawHeaders];
        while (headers.length < maxCols) headers.push("");

        const dataRows = dataLines.map((lineStr) => {
          const cells = parseRow(lineStr);
          while (cells.length < maxCols) cells.push("");
          return cells;
        });

        elements.push(
          <div
            key={`tbl-${i}`}
            className="overflow-x-auto my-4 border border-border-iron rounded-xl shadow-xs bg-surface/20 clear-both"
          >
            <table className="w-full min-w-[320px] text-left text-xs border-collapse">
              <thead className="bg-surface/90 border-b border-border-iron text-gold font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="px-3.5 py-2.5 whitespace-nowrap">
                      {renderInline(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border-iron/40">
                {dataRows.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    className="hover:bg-surface/50 transition-colors even:bg-surface/15"
                  >
                    {row.map((cell, cIdx) => (
                      <td
                        key={cIdx}
                        className="px-3.5 py-2 text-main/90 align-top leading-relaxed break-words"
                      >
                        {renderInline(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Listas con viñetas
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const listItems: string[] = [];
      while (
        i < lines.length &&
        (lines[i].trim().startsWith("- ") || lines[i].trim().startsWith("* "))
      ) {
        listItems.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="list-disc list-inside space-y-1 my-2 text-main/90">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Encabezados
    if (trimmed.startsWith("### ")) {
      elements.push(
        <h3 key={i} className="font-display font-bold text-base text-gold mt-3 mb-1">
          {renderInline(trimmed.slice(4))}
        </h3>
      );
      i++;
      continue;
    }
    if (trimmed.startsWith("## ")) {
      elements.push(
        <h2
          key={i}
          className="font-display font-bold text-lg text-gold mt-4 mb-1.5 border-b border-border-iron/60 pb-1"
        >
          {renderInline(trimmed.slice(3))}
        </h2>
      );
      i++;
      continue;
    }
    if (trimmed.startsWith("# ")) {
      elements.push(
        <h1 key={i} className="font-display font-bold text-xl text-gold mt-2 mb-2">
          {renderInline(trimmed.slice(2))}
        </h1>
      );
      i++;
      continue;
    }

    // Blockquotes
    if (trimmed.startsWith("> ")) {
      elements.push(
        <blockquote
          key={i}
          className="border-l-2 border-gold pl-3 py-1 my-2 italic text-muted bg-surface/40 rounded-r"
        >
          {renderInline(trimmed.slice(2))}
        </blockquote>
      );
      i++;
      continue;
    }

    // Separador horizontal
    if (trimmed === "---" || trimmed === "***") {
      elements.push(<hr key={i} className="border-border-iron my-3" />);
      i++;
      continue;
    }

    // Párrafo normal
    elements.push(
      <p key={i} className="leading-relaxed text-main/90 my-1.5">
        {renderInline(trimmed)}
      </p>
    );
    i++;
  }

  return <div className={`text-xs md:text-sm font-body ${className}`}>{elements}</div>;
};
