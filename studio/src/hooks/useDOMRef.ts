import {useRef} from 'react';

// I can't get TS type-checking to pass without hacks like this.

export function useAnchorRef() {
  return useRef<HTMLAnchorElement>(
    document.createElement('a'));
}

export function useDivRef() {
  return useRef<HTMLDivElement>(
    document.createElement('div'));
}

export function useInputRef() {
  return useRef<HTMLInputElement>(
    document.createElement('input'));
}

export function useSpanRef() {
  return useRef<HTMLSpanElement>(
    document.createElement('span'));
}
