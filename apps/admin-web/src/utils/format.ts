export function formatCount(value: number): string {
  return new Intl.NumberFormat("zh-CN").format(value);
}

export function joinOrDash(values: string[]): string {
  return values.length ? values.join("、") : "无";
}
