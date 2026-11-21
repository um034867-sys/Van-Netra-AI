/* eslint-disable */
declare module "leaflet" {
  export type LatLngExpression = [number, number] | { lat: number; lng: number };
  export type LatLngBoundsExpression = any;
  export type FitBoundsOptions = any;
  export interface MapOptions {
    center?: LatLngExpression;
    zoom?: number;
    scrollWheelZoom?: boolean;
    [key: string]: any;
  }
  export interface TileLayerOptions {
    attribution?: string;
    [key: string]: any;
  }
  export interface MarkerOptions {
    icon?: any;
    [key: string]: any;
  }
  export interface PolylineOptions {
    color?: string;
    weight?: number;
    dashArray?: string;
    opacity?: number;
    [key: string]: any;
  }
  export interface PopupOptions {
    [key: string]: any;
  }
  export class Map {
    [key: string]: any;
  }
  export class TileLayer {
    constructor(url: string, options?: TileLayerOptions);
    [key: string]: any;
  }
  export class Marker<P = any> {
    constructor(latlng: LatLngExpression, options?: MarkerOptions);
    [key: string]: any;
  }
  export class Polyline<P = any> {
    constructor(
      latlngs: LatLngExpression[] | LatLngExpression[][],
      options?: PolylineOptions
    );
    [key: string]: any;
  }
  export class Popup {
    [key: string]: any;
  }
  export class DivIcon {
    constructor(options?: any);
    [key: string]: any;
  }
  export function divIcon(options?: any): any;
  const L: {
    divIcon: (options?: any) => any;
    [key: string]: any;
  };
  export default L;
}
