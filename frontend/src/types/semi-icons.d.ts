// src/types/semi-icons.d.ts
declare module '@douyinfe/semi-icons' {
  import { ComponentType, CSSProperties } from 'react';
  
  export interface IconProps {
    size?: 'small' | 'default' | 'large' | number;
    style?: CSSProperties;
    className?: string;
    spin?: boolean;
    rotate?: number;
    onClick?: (event: React.MouseEvent<HTMLSpanElement>) => void;
  }
  
  // 常用图标
  export const IconUpload: ComponentType<IconProps>;
  export const IconSend: ComponentType<IconProps>;
  export const IconHome: ComponentType<IconProps>;
  export const IconUser: ComponentType<IconProps>;
  export const IconClose: ComponentType<IconProps>;
  export const IconCheck: ComponentType<IconProps>;
  export const IconLoading: ComponentType<IconProps>;
  
  // 如果图标很多，可以使用这个通用类型
  // export const IconUpload: any;
}