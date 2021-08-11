import React from 'react';
import * as BBox from 'studio/foundation/bbox';

// Pollen
// ======

export const Copy = () => <PollenSVG>
  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
</PollenSVG>;

export const Edit2 = () => <PollenSVG>
  <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
</PollenSVG>;

export const Edit3 = () => <PollenSVG>
  <path d="M12 20h9" />
  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
</PollenSVG>;

export const Plus = () => <PollenSVG>
  <line x1="12" y1="5" x2="12" y2="19" />
  <line x1="5" y1="12" x2="19" y2="12" />
</PollenSVG>;

export const Trash2 = () => <PollenSVG>
  <polyline points="3 6 5 6 21 6" />
  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  <line x1="10" y1="11" x2="10" y2="17" />
  <line x1="14" y1="11" x2="14" y2="17" />
</PollenSVG>;

export const XOctagon = () => <PollenSVG>
  <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2" />
  <line x1="15" y1="9" x2="9" y2="15" />
  <line x1="9" y1="9" x2="15" y2="15" />
</PollenSVG>;

// Bootstrap
// =========

export const CollectionPlay = () => <BootstrapSVG>
  <path d="M2 3a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 0-1h-11A.5.5 0 0 0 2 3zm2-2a.5.5 0 0 0 .5.5h7a.5.5 0 0 0 0-1h-7A.5.5 0 0 0 4 1zm2.765 5.576A.5.5 0 0 0 6 7v5a.5.5 0 0 0 .765.424l4-2.5a.5.5 0 0 0 0-.848l-4-2.5z"/>
  <path d="M1.5 14.5A1.5 1.5 0 0 1 0 13V6a1.5 1.5 0 0 1 1.5-1.5h13A1.5 1.5 0 0 1 16 6v7a1.5 1.5 0 0 1-1.5 1.5h-13zm13-1a.5.5 0 0 0 .5-.5V6a.5.5 0 0 0-.5-.5h-13A.5.5 0 0 0 1 6v7a.5.5 0 0 0 .5.5h13z"/>
</BootstrapSVG>;

export const FileEarmarkRuled = () => <BootstrapSVG>
  <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V9H3V2a1 1 0 0 1 1-1h5.5v2zM3 12v-2h2v2H3zm0 1h2v2H4a1 1 0 0 1-1-1v-1zm3 2v-2h7v1a1 1 0 0 1-1 1H6zm7-3H6v-2h7v2z"/>
</BootstrapSVG>;

export const HandIndex = () => <BootstrapSVG>
  <path d="M6.75 1a.75.75 0 0 1 .75.75V8a.5.5 0 0 0 1 0V5.467l.086-.004c.317-.012.637-.008.816.027.134.027.294.096.448.182.077.042.15.147.15.314V8a.5.5 0 1 0 1 0V6.435a4.9 4.9 0 0 1 .106-.01c.316-.024.584-.01.708.04.118.046.3.207.486.43.081.096.15.19.2.259V8.5a.5.5 0 0 0 1 0v-1h.342a1 1 0 0 1 .995 1.1l-.271 2.715a2.5 2.5 0 0 1-.317.991l-1.395 2.442a.5.5 0 0 1-.434.252H6.035a.5.5 0 0 1-.416-.223l-1.433-2.15a1.5 1.5 0 0 1-.243-.666l-.345-3.105a.5.5 0 0 1 .399-.546L5 8.11V9a.5.5 0 0 0 1 0V1.75A.75.75 0 0 1 6.75 1zM8.5 4.466V1.75a1.75 1.75 0 1 0-3.5 0v5.34l-1.2.24a1.5 1.5 0 0 0-1.196 1.636l.345 3.106a2.5 2.5 0 0 0 .405 1.11l1.433 2.15A1.5 1.5 0 0 0 6.035 16h6.385a1.5 1.5 0 0 0 1.302-.756l1.395-2.441a3.5 3.5 0 0 0 .444-1.389l.271-2.715a2 2 0 0 0-1.99-2.199h-.581a5.114 5.114 0 0 0-.195-.248c-.191-.229-.51-.568-.88-.716-.364-.146-.846-.132-1.158-.108l-.132.012a1.26 1.26 0 0 0-.56-.642 2.632 2.632 0 0 0-.738-.288c-.31-.062-.739-.058-1.05-.046l-.048.002zm2.094 2.025z"/>
</BootstrapSVG>;

export const PlayBtn = () => <BootstrapSVG>
  <path d="M6.79 5.093A.5.5 0 0 0 6 5.5v5a.5.5 0 0 0 .79.407l3.5-2.5a.5.5 0 0 0 0-.814l-3.5-2.5z"/>
  <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4zm15 0a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4z"/>
</BootstrapSVG>;

export const X = () => <BootstrapSVG viewBox="2 2 12 12">
  <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
</BootstrapSVG>;

// Other
// =====

export const MagicWand = () => (
  <svg
    width="24px"
    height="24px"

    xmlns="http://www.w3.org/2000/svg"
    version="1.1"
    x="0px"
    y="0px"
    viewBox="0 0 512 512"
    stroke="currentColor"
    fill="currentColor"
  >
    <g>
      <path d="M344.476,105.328L1.004,448.799L64.205,512l343.472-343.471L344.476,105.328z M290.594,201.792l53.882-53.882
        l20.619,20.619l-53.882,53.882L290.594,201.792z"/>
      <rect x="413.735" y="55.578" transform="matrix(0.7071 -0.7071 0.7071 0.7071 79.0342 332.0713)" width="53.255" height="30.11"/>
      <rect x="420.768" y="255.551" transform="matrix(0.7071 -0.7071 0.7071 0.7071 -72.2351 390.9691)" width="30.11" height="54.259"/>
      <rect x="213.158" y="48.098" transform="matrix(0.7071 -0.7071 0.7071 0.7071 13.767 183.3558)" width="30.11" height="53.922"/>
      <polygon points="510.735,163.868 456.446,163.868 456.446,193.979 510.735,193.979 510.996,193.979 510.996,163.868 		"/>
      <polygon points="317.017,0.018 317.017,54.307 347.128,54.307 347.128,0.018 347.128,0 		"/>
    </g>
  </svg>
);

export const MergeIcon = () => (
  <svg
    width="24px"
    height="24px"

    xmlns="http://www.w3.org/2000/svg"
    version="1.1"
    id="Capa_1"
    x="0px" y="0px" viewBox="0 0 360.853 360.853"
    stroke="currentColor"
    fill="currentColor"
  >
    <g>
      <polygon points="180.427,0 84.427,96 159.093,96 159.093,215.147 43.573,330.667 73.76,360.853 201.76,232.853 201.76,96 276.427,96"/>
      <rect x="244.415" y="257.818" transform="matrix(0.7071 -0.7071 0.7071 0.7071 -140.8924 278.5227)" width="42.69" height="103.03"/>
    </g>
  </svg>
);

export const PickBestIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24px"
    height="24px"
    version="1.1"
    id="Capa_1"
    x="0px" y="0px"
    viewBox="0 0 341.333 341.333"
    stroke="currentColor"
    fill="currentColor"
    style={{
      transform: 'rotate(180deg)'
    }}
  >
    <g>
			<polygon points="128,0 0,0 0,128 48.96,79.04 149.333,179.52 149.333,341.333 192,341.333 192,161.813 79.04,48.96 			"/>
			<polygon points="213.333,0 262.293,48.96 200.853,110.293 231.04,140.48 292.373,79.04 341.333,128 341.333,0 			"/>
    </g>
  </svg>
);

// Utils
// =====

type PollenSVGProps = {
  children: React.ReactNode;
};

function PollenSVG(props: PollenSVGProps) {
  return <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {props.children}
  </svg>;
}

type BootstrapSVGProps = {
  children: React.ReactNode;
  viewBox?: string;
};

function BootstrapSVG(props: BootstrapSVGProps) {
  return <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    fill="currentColor"
    viewBox={props.viewBox || '0 0 16 16'}
  >
    {props.children}
  </svg>;
}
