import { NextRequest, NextResponse } from 'next/server';
import { cycomCallKw } from '@/lib/cycomServer';

/**
 * Returns the cycom.tenant.* hints saved by Company Setup so downstream wizards can pre-fill
 * country / industry / pricing mode without re-asking the user.
 */
export async function POST(req: NextRequest) {
  async function getParam(key: string): Promise<string | null> {
    const res = await cycomCallKw(req, {
      model: 'ir.config_parameter',
      method: 'get_param',
      args: [key, false],
      kwargs: {},
    });
    const data = (await res.json()) as { result?: string | false | null; error?: { message?: string } };
    if (data.error || data.result === false || data.result == null) return null;
    return String(data.result);
  }

  try {
    const [industry, countryCode, pricingMode] = await Promise.all([
      getParam('cycom.tenant.industry'),
      getParam('cycom.tenant.country_code'),
      getParam('cycom.tenant.pricing_mode'),
    ]);
    return NextResponse.json({
      industry: industry ?? undefined,
      countryCode: countryCode ?? undefined,
      pricingMode: (pricingMode as 'tax_inclusive' | 'tax_exclusive' | undefined) ?? undefined,
    });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : 'failed' }, { status: 500 });
  }
}
