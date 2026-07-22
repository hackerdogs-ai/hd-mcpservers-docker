import React from 'react';

/**
 * Google Material Symbols (Outlined) icon.
 *
 * Usage: <Icon name="search" size={18} /> — `name` is a Material Symbols
 * ligature (see https://fonts.google.com/icons). Monochrome; inherits
 * `currentColor`. Prefer the standard sizes 16/18/20/24/32.
 */
export default function Icon({ name, size = 18, fill = false, className = '', style, ...rest }) {
  const standard = [16, 18, 20, 24, 32].includes(size);
  const sizeClass = standard ? `mi-${size}` : '';
  const mergedStyle = standard ? style : { fontSize: `${size}px`, ...style };
  const classes = ['mi', sizeClass, fill ? 'fill' : '', className].filter(Boolean).join(' ');
  return (
    <span className={classes} style={mergedStyle} aria-hidden="true" {...rest}>
      {name}
    </span>
  );
}
