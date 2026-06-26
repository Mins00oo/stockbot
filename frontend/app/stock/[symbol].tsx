import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import {
  SafeAreaView,
  useSafeAreaInsets,
} from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { CHART_RANGES, type ChartRange } from "@/api/stocks";
import { BackButton, Card, LogoChip, PrimaryButton } from "@/components";
import { PriceChart } from "@/components/PriceChart";
import { useHoldings } from "@/hooks/useHoldings";
import {
  useChart,
  useOrderbook,
  useQuote,
  useStockDetail,
  useTrades,
} from "@/hooks/useStock";
import {
  asCurrency,
  fmtInt,
  marketCapStr,
  money,
  qty,
  signedMoney,
  signedPct,
  timeOfDay,
} from "@/lib/format";
import { colors, pnlColor, shadow } from "@/theme/tokens";
import type {
  Currency,
  Holding,
  Orderbook,
  Quote,
  StockDetail,
  TradesResponse,
  TradingWarning,
} from "@/types/api";

const DASH = "—";
const ASK_BG = "#E7F0FF"; // 매도 잔량 바 (blue tint)
const BID_BG = "#FFE9EC"; // 매수 잔량 바 (red tint)
const TRACK_BG = "#F8F9FB"; // 기간 선택 트랙

type BookTab = "호가" | "체결";

/** Warning banner palette per type group (per DETAIL_SCREEN.md §5). */
function warnColors(w: TradingWarning): { fg: string; bg: string } {
  const t = w.type;
  if (t === "INVESTMENT_RISK") return { fg: "#F03E3E", bg: "#FFE3E3" };
  if (t === "OVERHEATED") return { fg: "#E8590C", bg: "#FFF0E6" };
  if (t.startsWith("VI")) return { fg: "#1098AD", bg: "#E3FAFC" };
  return { fg: "#F08C00", bg: "#FFF9DB" }; // 투자주의/경고·기타
}

export default function StockDetailScreen() {
  const params = useLocalSearchParams<{
    symbol: string;
    market?: string;
    name?: string;
  }>();
  const symbol = String(params.symbol ?? "");
  const market = params.market;

  const insets = useSafeAreaInsets();
  const { width: winW } = useWindowDimensions();
  const chartW = winW - 72; // screen pad 20*2 + card pad 16*2

  const [range, setRange] = useState<ChartRange>("3M");
  const [bookTab, setBookTab] = useState<BookTab>("호가");
  const [starred, setStarred] = useState(false);

  const detailQ = useStockDetail(symbol, market);
  const quoteQ = useQuote(symbol, market);
  const chartQ = useChart(symbol, range);
  const obQ = useOrderbook(symbol, bookTab === "호가");
  const trQ = useTrades(symbol, bookTab === "체결");
  const holding = useHoldings().data?.holdings.find((h) => h.symbol === symbol);

  const detail = detailQ.data;
  const quote = quoteQ.data;

  const headerName = detail?.name ?? params.name ?? symbol;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }} edges={["top"]}>
      {/* (1) header */}
      <View
        style={{
          height: 52,
          paddingHorizontal: 14,
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <BackButton />
        <Text
          numberOfLines={1}
          style={{
            flex: 1,
            textAlign: "center",
            fontSize: 15,
            fontWeight: "700",
            color: colors.text.strong,
          }}
        >
          {headerName}
        </Text>
        <StarButton starred={starred} onToggle={() => setStarred((s) => !s)} />
      </View>

      {detailQ.isLoading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : detailQ.isError || !detail ? (
        <DetailError error={detailQ.error} onRetry={() => detailQ.refetch()} />
      ) : (
        <>
          <ScrollView
            contentContainerStyle={{
              paddingBottom: 84 + insets.bottom,
            }}
            showsVerticalScrollIndicator={false}
          >
            {/* (2) 종목 헤더 */}
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                gap: 12,
                paddingHorizontal: 20,
                paddingTop: 6,
              }}
            >
              <LogoChip
                symbol={detail.symbol}
                name={detail.name}
                size={46}
                radiusPx={14}
                fontSize={18}
              />
              <View style={{ flex: 1, minWidth: 0 }}>
                <Text
                  style={{ fontSize: 13, fontWeight: "600", color: colors.text.dim }}
                >
                  {(detail.market === "KR" ? "🇰🇷 " : "🇺🇸 ") +
                    (detail.exchange ?? (detail.market === "KR" ? "국내" : "미국")) +
                    " · " +
                    detail.symbol}
                </Text>
                <Text
                  numberOfLines={1}
                  style={{
                    fontSize: 18,
                    fontWeight: "800",
                    color: colors.text.strong,
                    marginTop: 2,
                  }}
                >
                  {detail.name}
                </Text>
              </View>
            </View>

            {/* (3) 현재가 블록 */}
            <PriceBlock detail={detail} quote={quote} loading={quoteQ.isLoading} />

            {/* (4) 거래량·상한가·하한가 스트립 */}
            <InfoStrip detail={detail} quote={quote} />

            {/* (5) 거래경고 — KR, 경고 있을 때만 */}
            {detail.market === "KR" && detail.warnings.length > 0 ? (
              <View style={{ paddingHorizontal: 20, marginTop: 12, gap: 8 }}>
                {detail.warnings.map((w) => {
                  const c = warnColors(w);
                  return (
                    <View
                      key={w.type}
                      style={{
                        backgroundColor: c.bg,
                        borderRadius: 14,
                        padding: 14,
                      }}
                    >
                      <Text style={{ fontSize: 13.5, fontWeight: "800", color: c.fg }}>
                        ⚠️ 거래경고 · {w.label}
                      </Text>
                      <Text
                        style={{
                          fontSize: 12.5,
                          color: colors.text.body,
                          marginTop: 4,
                          lineHeight: 18,
                        }}
                      >
                        해당 종목은 {w.label} 상태예요. 투자 전 위험을 꼭 확인하세요.
                      </Text>
                    </View>
                  );
                })}
              </View>
            ) : null}

            {/* (6) 차트 카드 */}
            <ChartCard
              symbol={symbol}
              range={range}
              setRange={setRange}
              width={chartW}
              chartQ={chartQ}
              currency={asCurrency(quote?.currency ?? detail.currency)}
            />

            {/* (7) 호가 / 체결 카드 */}
            <BookCard
              tab={bookTab}
              setTab={setBookTab}
              orderbook={obQ.data}
              trades={trQ.data}
              loading={bookTab === "호가" ? obQ.isLoading : trQ.isLoading}
              prevClose={detail.prevClose}
              currency={asCurrency(quote?.currency ?? detail.currency)}
            />

            {/* (8) 내 보유 현황 — 보유 종목만 */}
            {holding ? <HoldingCard holding={holding} /> : null}

            {/* (9) 종목 정보 */}
            <InfoCard detail={detail} />
          </ScrollView>

          {/* (11) 하단 고정 액션바 */}
          <View
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: colors.card,
              borderTopWidth: 1,
              borderTopColor: colors.edge,
              flexDirection: "row",
              gap: 10,
              paddingHorizontal: 16,
              paddingTop: 10,
              paddingBottom: 10 + insets.bottom,
            }}
          >
            <Pressable
              onPress={() => setStarred((s) => !s)}
              style={{
                width: 54,
                height: 52,
                borderRadius: 14,
                backgroundColor: "#F2F4F6",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Text style={{ fontSize: 22, color: starred ? colors.star : colors.starOff }}>
                {starred ? "★" : "☆"}
              </Text>
            </Pressable>
            <Pressable
              // 매수 주문 API 미구현 — 주문 플로우 붙으면 연결.
              onPress={() => {}}
              style={{
                flex: 1,
                height: 52,
                borderRadius: 14,
                backgroundColor: colors.primary,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Text style={{ fontSize: 16, fontWeight: "700", color: "#fff" }}>
                매수하기
              </Text>
            </Pressable>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

/* ----------------------------- sections ----------------------------- */

function StarButton({
  starred,
  onToggle,
}: {
  starred: boolean;
  onToggle: () => void;
}) {
  return (
    <Pressable
      onPress={onToggle}
      hitSlop={8}
      style={{ width: 32, height: 32, alignItems: "center", justifyContent: "center" }}
    >
      <Text style={{ fontSize: 22, color: starred ? colors.star : colors.starOff }}>
        {starred ? "★" : "☆"}
      </Text>
    </Pressable>
  );
}

function PriceBlock({
  detail,
  quote,
  loading,
}: {
  detail: StockDetail;
  quote?: Quote;
  loading: boolean;
}) {
  const cur = asCurrency(quote?.currency ?? detail.currency);
  const isUS = detail.market === "US";
  const change = quote?.change ?? null;
  const rate = quote?.changeRate ?? null;
  const up = (change ?? 0) >= 0;
  const color = pnlColor(change ?? 0);

  return (
    <View style={{ paddingHorizontal: 20, paddingTop: 14 }}>
      <Text
        style={{
          fontSize: 32,
          fontWeight: "800",
          color: colors.text.strong,
          letterSpacing: -1,
        }}
      >
        {quote ? money(cur, quote.price) : loading ? "…" : DASH}
      </Text>
      <View
        style={{ flexDirection: "row", alignItems: "center", gap: 8, marginTop: 4 }}
      >
        <Text style={{ fontSize: 15, fontWeight: "700", color }}>
          {rate != null
            ? `${up ? "▲" : "▼"} ${Math.abs(rate).toFixed(2)}%`
            : DASH}
          {change != null ? `   ${signedMoney(cur, change)}` : ""}
        </Text>
        {isUS && quote?.krwPrice != null ? (
          <Text style={{ fontSize: 13, fontWeight: "600", color: colors.text.dimmer }}>
            ₩{fmtInt(quote.krwPrice)}
          </Text>
        ) : null}
      </View>
    </View>
  );
}

function InfoStrip({ detail, quote }: { detail: StockDetail; quote?: Quote }) {
  const cur = asCurrency(quote?.currency ?? detail.currency);
  const cells: { label: string; value: string; color: string }[] = [
    {
      label: "거래량",
      value: quote?.volume != null ? fmtInt(quote.volume) : DASH,
      color: colors.text.strong,
    },
    {
      label: "상한가",
      value:
        detail.priceLimits.upper != null
          ? money(cur, detail.priceLimits.upper)
          : DASH,
      color: colors.up,
    },
    {
      label: "하한가",
      value:
        detail.priceLimits.lower != null
          ? money(cur, detail.priceLimits.lower)
          : DASH,
      color: colors.down,
    },
  ];
  return (
    <Card style={{ marginHorizontal: 20, marginTop: 14 }} rounded={16} padding={0}>
      <View style={{ flexDirection: "row" }}>
        {cells.map((c, i) => (
          <View
            key={c.label}
            style={{
              flex: 1,
              paddingVertical: 14,
              alignItems: "center",
              borderLeftWidth: i === 0 ? 0 : 1,
              borderLeftColor: colors.divider,
            }}
          >
            <Text style={{ fontSize: 11.5, fontWeight: "600", color: colors.text.dim }}>
              {c.label}
            </Text>
            <Text
              style={{ fontSize: 14, fontWeight: "700", color: c.color, marginTop: 4 }}
            >
              {c.value}
            </Text>
          </View>
        ))}
      </View>
    </Card>
  );
}

function ChartCard({
  range,
  setRange,
  width,
  chartQ,
  currency,
}: {
  symbol: string;
  range: ChartRange;
  setRange: (r: ChartRange) => void;
  width: number;
  chartQ: ReturnType<typeof useChart>;
  currency: Currency;
}) {
  const data = chartQ.data;
  const points = data?.points ?? [];
  const closes = points.map((p) => p.close);
  const volumes = points.map((p) => p.volume);
  const times = points.map((p) => p.t);
  const periodReturn = data?.periodReturn ?? null;
  const up = (periodReturn ?? 0) >= 0;
  const rangeLabel =
    CHART_RANGES.find((r) => r.key === range)?.label ?? range;

  const fmtPrice = (v: number) => money(currency, v);
  const fmtStamp = (t: string) => {
    const d = new Date(t);
    if (isNaN(d.getTime())) return t;
    const p = (x: number) => String(x).padStart(2, "0");
    return range === "1D"
      ? `${p(d.getHours())}:${p(d.getMinutes())}`
      : `${d.getFullYear()}.${p(d.getMonth() + 1)}.${p(d.getDate())}`;
  };

  return (
    <Card style={{ marginHorizontal: 20, marginTop: 12 }} rounded={18} padding={16}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Text style={{ fontSize: 14, fontWeight: "800", color: colors.text.strong }}>
          차트
        </Text>
        {periodReturn != null ? (
          <Text
            style={{
              fontSize: 13,
              fontWeight: "700",
              color: up ? colors.up : colors.down,
            }}
          >
            {rangeLabel} {periodReturn >= 0 ? "+" : ""}
            {periodReturn.toFixed(2)}%
          </Text>
        ) : null}
      </View>

      <View style={{ marginTop: 12, minHeight: 128, justifyContent: "center" }}>
        {chartQ.isLoading ? (
          <ActivityIndicator color={colors.primary} />
        ) : points.length >= 1 ? (
          <PriceChart
            closes={closes}
            volumes={volumes}
            times={times}
            up={up}
            width={width}
            formatPrice={fmtPrice}
            formatStamp={fmtStamp}
          />
        ) : (
          <Text
            style={{ fontSize: 13, color: colors.text.dim, textAlign: "center" }}
          >
            차트 데이터가 없어요
          </Text>
        )}
      </View>

      {/* 기간 선택 바 */}
      <View
        style={{
          flexDirection: "row",
          backgroundColor: TRACK_BG,
          borderRadius: 12,
          padding: 4,
          marginTop: 14,
        }}
      >
        {CHART_RANGES.map((r) => {
          const active = r.key === range;
          return (
            <Pressable
              key={r.key}
              onPress={() => setRange(r.key)}
              style={{
                flex: 1,
                paddingVertical: 11,
                borderRadius: 9,
                alignItems: "center",
                backgroundColor: active ? colors.primaryBg : "transparent",
              }}
            >
              <Text
                style={{
                  fontSize: 13,
                  fontWeight: active ? "700" : "600",
                  color: active ? colors.primary : colors.text.dim,
                }}
              >
                {r.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text
        style={{
          fontSize: 11,
          color: colors.text.dimmer,
          textAlign: "center",
          marginTop: 10,
        }}
      >
        1일·1주·1달·3달·1년 · 실시간 스트리밍은 제공되지 않아요
      </Text>
    </Card>
  );
}

function BookCard({
  tab,
  setTab,
  orderbook,
  trades,
  loading,
  prevClose,
  currency,
}: {
  tab: BookTab;
  setTab: (t: BookTab) => void;
  orderbook?: Orderbook;
  trades?: TradesResponse;
  loading: boolean;
  prevClose: number | null;
  currency: Currency;
}) {
  return (
    <Card style={{ marginHorizontal: 20, marginTop: 12 }} rounded={18} padding={16}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Text style={{ fontSize: 14, fontWeight: "800", color: colors.text.strong }}>
          {tab === "호가" ? "호가 10단계" : "최근 체결"}
        </Text>
        <Segment tab={tab} setTab={setTab} />
      </View>

      <View style={{ marginTop: 12, minHeight: 80, justifyContent: "center" }}>
        {loading ? (
          <ActivityIndicator color={colors.primary} />
        ) : tab === "호가" ? (
          <OrderbookView
            orderbook={orderbook}
            prevClose={prevClose}
            currency={currency}
          />
        ) : (
          <TradesView trades={trades} prevClose={prevClose} currency={currency} />
        )}
      </View>

      <Text
        style={{
          fontSize: 11,
          color: colors.text.dimmer,
          textAlign: "center",
          marginTop: 10,
        }}
      >
        10단계 호가 · 최근 체결 스냅샷 (실시간 아님)
      </Text>
    </Card>
  );
}

function Segment({ tab, setTab }: { tab: BookTab; setTab: (t: BookTab) => void }) {
  return (
    <View
      style={{
        flexDirection: "row",
        backgroundColor: TRACK_BG,
        borderRadius: 9,
        padding: 3,
      }}
    >
      {(["호가", "체결"] as BookTab[]).map((t) => {
        const active = t === tab;
        return (
          <Pressable
            key={t}
            onPress={() => setTab(t)}
            style={{
              paddingHorizontal: 14,
              paddingVertical: 6,
              borderRadius: 7,
              backgroundColor: active ? colors.card : "transparent",
              ...(active ? shadow.card : null),
            }}
          >
            <Text
              style={{
                fontSize: 12.5,
                fontWeight: active ? "700" : "600",
                color: active ? colors.text.strong : colors.text.dim,
              }}
            >
              {t}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function OrderbookView({
  orderbook,
  prevClose,
  currency,
}: {
  orderbook?: Orderbook;
  prevClose: number | null;
  currency: Currency;
}) {
  if (!orderbook || (orderbook.asks.length === 0 && orderbook.bids.length === 0)) {
    return (
      <Text style={{ fontSize: 13, color: colors.text.dim, textAlign: "center" }}>
        호가 데이터가 없어요
      </Text>
    );
  }
  const asks = orderbook.asks.slice(0, 10);
  const bids = orderbook.bids.slice(0, 10);
  const maxVol = Math.max(
    1,
    ...asks.map((a) => a.volume),
    ...bids.map((b) => b.volume),
  );

  // 매도(ask): 가격 높은 게 위로 → reverse. 매수(bid): 가격 높은(best) 게 위로.
  const askRows = [...asks].reverse();

  return (
    <View>
      {askRows.map((lv, i) => (
        <BookRow
          key={`a${i}`}
          side="ask"
          price={lv.price}
          volume={lv.volume}
          maxVol={maxVol}
          prevClose={prevClose}
          currency={currency}
        />
      ))}
      {bids.map((lv, i) => (
        <BookRow
          key={`b${i}`}
          side="bid"
          price={lv.price}
          volume={lv.volume}
          maxVol={maxVol}
          prevClose={prevClose}
          currency={currency}
        />
      ))}
    </View>
  );
}

function BookRow({
  side,
  price,
  volume,
  maxVol,
  prevClose,
  currency,
}: {
  side: "ask" | "bid";
  price: number;
  volume: number;
  maxVol: number;
  prevClose: number | null;
  currency: Currency;
}) {
  const priceColor =
    prevClose == null
      ? colors.text.strong
      : price >= prevClose
        ? colors.up
        : colors.down;
  const barPct = Math.min(100, Math.round((volume / maxVol) * 100));
  const barColor = side === "ask" ? ASK_BG : BID_BG;
  const qtyColor = side === "ask" ? colors.down : colors.up;
  const barPos = side === "ask" ? { right: 0 } : { left: 0 };

  const qtyCell = (
    <View style={{ flex: 1, height: 26, justifyContent: "center" }}>
      <View
        style={{
          position: "absolute",
          top: 3,
          bottom: 3,
          ...barPos,
          width: `${barPct}%`,
          backgroundColor: barColor,
          borderRadius: 4,
        }}
      />
      <Text
        style={{
          fontSize: 12,
          fontWeight: "600",
          color: qtyColor,
          textAlign: side === "ask" ? "right" : "left",
          paddingHorizontal: 6,
        }}
      >
        {fmtInt(volume)}
      </Text>
    </View>
  );

  return (
    <View style={{ flexDirection: "row", alignItems: "center" }}>
      {side === "ask" ? qtyCell : <View style={{ flex: 1 }} />}
      <Text
        style={{
          width: 92,
          textAlign: "center",
          fontSize: 12.5,
          fontWeight: "700",
          color: priceColor,
          paddingVertical: 4,
        }}
      >
        {money(currency, price)}
      </Text>
      {side === "bid" ? qtyCell : <View style={{ flex: 1 }} />}
    </View>
  );
}

function TradesView({
  trades,
  prevClose,
  currency,
}: {
  trades?: TradesResponse;
  prevClose: number | null;
  currency: Currency;
}) {
  const rows = trades?.trades ?? [];
  if (rows.length === 0) {
    return (
      <Text style={{ fontSize: 13, color: colors.text.dim, textAlign: "center" }}>
        체결 데이터가 없어요
      </Text>
    );
  }
  return (
    <View>
      <View style={{ flexDirection: "row", paddingBottom: 6 }}>
        {["체결시각", "체결가", "체결량"].map((h, i) => (
          <Text
            key={h}
            style={{
              flex: 1,
              fontSize: 11.5,
              color: colors.text.dim,
              fontWeight: "600",
              textAlign: i === 0 ? "left" : i === 1 ? "center" : "right",
            }}
          >
            {h}
          </Text>
        ))}
      </View>
      {rows.slice(0, 20).map((t, i) => {
        const c =
          prevClose == null
            ? colors.text.strong
            : t.price >= prevClose
              ? colors.up
              : colors.down;
        return (
          <View key={i} style={{ flexDirection: "row", paddingVertical: 4 }}>
            <Text style={{ flex: 1, fontSize: 12.5, color: colors.text.sub }}>
              {timeOfDay(t.time)}
            </Text>
            <Text
              style={{
                flex: 1,
                fontSize: 12.5,
                fontWeight: "700",
                color: c,
                textAlign: "center",
              }}
            >
              {money(currency, t.price)}
            </Text>
            <Text
              style={{
                flex: 1,
                fontSize: 12.5,
                color: colors.text.body,
                textAlign: "right",
              }}
            >
              {fmtInt(t.volume)}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

function HoldingCard({ holding }: { holding: Holding }) {
  const cur = holding.currency;
  const isUS = holding.market === "US";
  return (
    <Card style={{ marginHorizontal: 20, marginTop: 12 }} rounded={18} padding={16}>
      <Text
        style={{
          fontSize: 14,
          fontWeight: "800",
          color: colors.text.strong,
          marginBottom: 6,
        }}
      >
        내 보유 현황
      </Text>
      <KV label="보유 수량" value={`${qty(holding.quantity)}주`} />
      <KV label="평균 단가" value={money(cur, holding.avgPrice)} />
      <KV
        label="평가 금액"
        value={money(cur, holding.evalAmount)}
        sub={isUS ? `₩${fmtInt(holding.evalAmountKrw)}` : undefined}
      />
      <KV
        label="평가 손익"
        value={`${signedMoney(cur, holding.pnl)} (${signedPct(holding.pnlRate)})`}
        color={pnlColor(holding.pnl)}
      />
    </Card>
  );
}

function InfoCard({ detail }: { detail: StockDetail }) {
  const cur = asCurrency(detail.currency);
  const f = detail.fundamentals;
  const isUS = detail.market === "US";
  const w52 =
    f.week52Low == null && f.week52High == null
      ? DASH
      : `${f.week52Low != null ? money(cur, f.week52Low) : DASH} ~ ${
          f.week52High != null ? money(cur, f.week52High) : DASH
        }`;

  return (
    <Card style={{ marginHorizontal: 20, marginTop: 12 }} rounded={18} padding={16}>
      <Text
        style={{
          fontSize: 14,
          fontWeight: "800",
          color: colors.text.strong,
          marginBottom: 6,
        }}
      >
        종목 정보
      </Text>
      <KV
        label="시가총액"
        value={f.marketCap != null ? marketCapStr(cur, f.marketCap) : DASH}
      />
      {isUS ? (
        <>
          <KV label="PER" value={f.per != null ? f.per.toFixed(2) : DASH} />
          <KV label="PBR" value={f.pbr != null ? f.pbr.toFixed(2) : DASH} />
          <KV label="EPS" value={f.eps != null ? money("USD", f.eps) : DASH} />
          <KV
            label="배당수익률"
            value={f.dividendYield != null ? `${f.dividendYield.toFixed(2)}%` : DASH}
          />
          {detail.industry ? <KV label="산업" value={detail.industry} /> : null}
        </>
      ) : null}
      <KV label="52주 최저~최고" value={w52} />
    </Card>
  );
}

function KV({
  label,
  value,
  color,
  sub,
}: {
  label: string;
  value: string;
  color?: string;
  sub?: string;
}) {
  return (
    <View
      style={{
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "flex-start",
        paddingVertical: 9,
        borderTopWidth: 1,
        borderTopColor: colors.divider,
      }}
    >
      <Text style={{ fontSize: 13.5, color: colors.text.dim, fontWeight: "600" }}>
        {label}
      </Text>
      <View style={{ alignItems: "flex-end" }}>
        <Text
          style={{ fontSize: 14.5, fontWeight: "700", color: color ?? colors.text.strong }}
        >
          {value}
        </Text>
        {sub ? (
          <Text style={{ fontSize: 12, color: colors.text.dimmer, marginTop: 1 }}>
            {sub}
          </Text>
        ) : null}
      </View>
    </View>
  );
}

function DetailError({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry: () => void;
}) {
  const notConnected =
    error instanceof ApiError && error.code === "NOT_CONNECTED";
  const message =
    error instanceof ApiError ? error.message : "종목 정보를 불러오지 못했어요";
  return (
    <View
      style={{
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        paddingHorizontal: 40,
      }}
    >
      <Text style={{ fontSize: 32 }}>{notConnected ? "🔌" : "⚠️"}</Text>
      <Text
        style={{
          marginTop: 14,
          fontSize: 15,
          fontWeight: "700",
          color: colors.text.body,
          textAlign: "center",
        }}
      >
        {message}
      </Text>
      <View style={{ marginTop: 20, width: 200 }}>
        {notConnected ? (
          <PrimaryButton
            label="계좌 연결하기"
            onPress={() => router.replace("/onboarding/toss-key")}
          />
        ) : (
          <PrimaryButton label="다시 시도" onPress={onRetry} />
        )}
      </View>
    </View>
  );
}
