// src/types/semi-ui.d.ts
import { ComponentType, ReactNode, HTMLAttributes } from 'react';

declare module '@douyinfe/semi-ui' {
  // 覆盖 Card 组件的类型定义
  export interface CardProps extends HTMLAttributes<HTMLDivElement> {
    children?: ReactNode;
    className?: string;
    style?: React.CSSProperties;
    title?: ReactNode;
    header?: ReactNode;
    headerExtra?: ReactNode;
    footer?: ReactNode;
    headerStyle?: React.CSSProperties;
    bodyStyle?: React.CSSProperties;
    footerStyle?: React.CSSProperties;
    cover?: ReactNode;
    actions?: ReactNode[];
    hoverable?: boolean;
    bordered?: boolean;
    shadow?: boolean | string;
    loading?: boolean;
    onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  }

  export const Card: ComponentType<CardProps>;
  
  // 保留其他组件的原有类型
  export const Button: ComponentType<any>;
  export const Space: ComponentType<any>;
  export const Upload: ComponentType<any>;
  export const Tag: ComponentType<any>;
  export const Progress: ComponentType<any>;
  export const Toast: any;
}