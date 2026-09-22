import React from "react";

/**
 * PaperPilot AI mark: a neuron / neural-network node.
 * One glowing center node (the "soma") connected to five outer nodes
 * (the "dendrites"), with two faint cross-links for the network feel.
 */
export function LogoMark({ size = 28, className = "" }) {
  const gradId = "ppGradFixed"; // stable id; fine even with multiple instances on a page
  const g = `url(#${gradId})`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient
          id={gradId}
          x1="6"
          y1="42"
          x2="42"
          y2="6"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#5B4BDB" />
          <stop offset="1" stopColor="#0891B2" />
        </linearGradient>
      </defs>

      {/* faint cross-links between outer nodes */}
      <line
        x1="39"
        y1="11"
        x2="42"
        y2="29"
        stroke={g}
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity="0.45"
      />
      <line
        x1="28"
        y1="42"
        x2="10"
        y2="35"
        stroke={g}
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity="0.45"
      />

      {/* connections from the center node to each outer node */}
      <line
        x1="24"
        y1="24"
        x2="9"
        y2="13"
        stroke={g}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <line
        x1="24"
        y1="24"
        x2="39"
        y2="11"
        stroke={g}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <line
        x1="24"
        y1="24"
        x2="42"
        y2="29"
        stroke={g}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <line
        x1="24"
        y1="24"
        x2="28"
        y2="42"
        stroke={g}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <line
        x1="24"
        y1="24"
        x2="10"
        y2="35"
        stroke={g}
        strokeWidth="2.2"
        strokeLinecap="round"
      />

      {/* outer nodes */}
      <circle
        cx="9"
        cy="13"
        r="3.6"
        fill="#FFFFFF"
        stroke={g}
        strokeWidth="2.2"
      />
      <circle
        cx="39"
        cy="11"
        r="3.6"
        fill="#FFFFFF"
        stroke={g}
        strokeWidth="2.2"
      />
      <circle
        cx="42"
        cy="29"
        r="3.6"
        fill="#FFFFFF"
        stroke={g}
        strokeWidth="2.2"
      />
      <circle
        cx="28"
        cy="42"
        r="3.6"
        fill="#FFFFFF"
        stroke={g}
        strokeWidth="2.2"
      />
      <circle
        cx="10"
        cy="35"
        r="3.6"
        fill="#FFFFFF"
        stroke={g}
        strokeWidth="2.2"
      />

      {/* center node */}
      <circle cx="24" cy="24" r="6.4" fill={g} />
      <circle cx="24" cy="24" r="2.3" fill="#FFFFFF" opacity="0.9" />
    </svg>
  );
}

/** Icon + wordmark, used in the sidebar and the landing screen. */
export function Brand({ size = 26, showSuffix = false, className = "" }) {
  return (
    <span className={`brand-mark ${className}`}>
      <LogoMark size={size} />
      <span className="wordmark">
        Paper<em>Pilot</em>
        {showSuffix ? " AI" : ""}
      </span>
    </span>
  );
}

export default LogoMark;
