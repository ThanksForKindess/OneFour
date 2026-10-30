import io
from decimal import Decimal, ROUND_HALF_UP

import qrcode
import streamlit as st

st.set_page_config(page_title="장보기 알림메모", page_icon="🛒", layout="centered", initial_sidebar_state="collapsed")

CATEGORIES = ["🥬 야채", "🍎 과일", "🥩 육류", "🐟 수산물", "🥚 유제품·달걀", "🍚 쌀·잡곡", "🍜 가공식품", "🧂 양념", "🧻 생활용품", "🛍️ 기타"]
PRIORITIES = {1: "1 · 꼭 필요", 2: "2 · 가격이 괜찮으면", 3: "3 · 비싸면 생략"}


def purchase_total(unit_price, quantity):
    return int((Decimal(str(unit_price)) * Decimal(str(quantity))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def money(value):
    return f"{value:,}원"


def init_state():
    defaults = {"pending": [], "cart": [], "next_id": 1, "notice": "", "share_url": ""}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()
st.markdown("""
<style>
.block-container {max-width:560px; padding:1rem .85rem .6rem;}
header[data-testid="stHeader"] {height:0; min-height:0;}
[data-testid="stMainBlockContainer"] {padding-top:.8rem;}
[data-testid="stVerticalBlock"] {gap:.45rem;}
h1 {font-size:1.35rem !important; padding:0 !important;}
p {margin-bottom:.25rem;}
[data-testid="stCaptionContainer"] {font-size:.78rem;}
div[data-testid="stMetric"] {background:#eef7f0; border-radius:12px; padding:8px 12px;}
[data-testid="stMetricValue"] {font-size:1.65rem;}
[data-testid="stForm"] {padding:.65rem; border-radius:12px;}
[data-testid="stHorizontalBlock"] {gap:.45rem;}
@media (max-width:640px) {
  [data-testid="stHorizontalBlock"] {flex-wrap:nowrap !important;}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width:0 !important; width:0 !important; flex:1 1 0 !important;}
  .stButton button, .stFormSubmitButton button {padding:.35rem .4rem; min-height:2.4rem;}
}
</style>
""", unsafe_allow_html=True)

heading, qr_column = st.columns([4, 1])
with heading:
    st.title("🛒 장보기 알림메모")
with qr_column:
    with st.popover("QR"):
        st.caption("배포한 앱의 공개 주소를 입력하세요. QR을 휴대폰 카메라로 스캔하면 앱이 열립니다.")
        url = st.text_input("공개 앱 주소", key="share_url", placeholder="https://your-app.streamlit.app")
        if url.strip().startswith("https://"):
            qr = qrcode.make(url.strip())
            buffer = io.BytesIO()
            qr.save(buffer, format="PNG")
            st.image(buffer.getvalue(), width=220)
        elif url.strip():
            st.warning("https:// 로 시작하는 공개 주소를 입력하세요.")
        st.caption("QR은 앱 주소만 공유합니다. 다른 휴대폰의 메모와 자동 동기화되지는 않습니다.")

pending = st.session_state.pending
cart = st.session_state.cart
total = sum(item["total"] for item in cart)
st.metric("현재 카트 총액", money(total), help="개당 가격 × 수량을 원 단위 반올림한 금액의 합계입니다.")
st.caption(f"남은 메모 {len(pending)}개 · 카트 {len(cart)}건 | 1 필수 · 2 적정가 · 3 선택")

add_col, cart_col = st.columns(2)
with add_col:
    with st.popover("＋ 상품 추가", use_container_width=True):
        with st.form("add_item", clear_on_submit=True):
            category = st.selectbox("카테고리", CATEGORIES)
            name = st.text_input("상품명", max_chars=60, placeholder="예: 사과 1봉, 우유 1L")
            priority = st.selectbox("중요도", [1, 2, 3], format_func=PRIORITIES.get, index=1)
            ceiling = st.number_input("개당 희망 상한가 (원, 0이면 미지정)", min_value=0, max_value=100000000, step=100, value=0)
            added = st.form_submit_button("메모에 추가", use_container_width=True)
        if added:
            if not name.strip():
                st.warning("상품명을 입력해주세요.")
            else:
                pending.append({"id": st.session_state.next_id, "category": category, "name": name.strip(), "priority": priority, "ceiling": ceiling})
                st.session_state.next_id += 1
                st.session_state.notice = "상품을 메모에 추가했어요."
                st.rerun()
with cart_col:
    with st.popover(f"🧺 카트 {len(cart)}건", use_container_width=True):
        st.markdown(f"**합계 {money(total)}**")
        if not cart:
            st.caption("구매를 기록하면 여기에 표시됩니다.")
        else:
            for entry in reversed(cart):
                st.caption(f"{entry['name']} · {money(entry['unit_price'])} × {entry['quantity']:g} = {money(entry['total'])}")
            choice = st.selectbox("잘못 담은 항목 되돌리기", [c["id"] for c in cart], format_func=lambda ident: next(f"{c['name']} · {money(c['total'])}" for c in cart if c['id'] == ident), key="undo_choice")
            if st.button("선택 항목을 메모로 복원", use_container_width=True):
                item = next(c for c in cart if c["id"] == choice)
                pending.append({k: item[k] for k in ["id", "category", "name", "priority", "ceiling"]})
                st.session_state.cart = [c for c in cart if c["id"] != choice]
                st.session_state.notice = "구매를 취소하고 메모로 복원했어요. 총액도 차감했어요."
                st.rerun()

if st.session_state.notice:
    st.caption("✓ " + st.session_state.notice)
    st.session_state.notice = ""

if not pending:
    st.info("위의 ‘＋ 상품 추가’로 장볼 상품을 적어주세요." if not cart else "남은 메모가 없어요. 카트에서 구매 내역을 확인하세요.")
else:
    ordered = sorted(pending, key=lambda x: (x["priority"], x["id"]))
    by_id = {item["id"]: item for item in ordered}
    selected = st.selectbox("살 상품 선택 · 중요도순", list(by_id), format_func=lambda ident: f"[{by_id[ident]['priority']}] {by_id[ident]['category']} · {by_id[ident]['name']}", key="selected_item")
    item = by_id[selected]
    if item["priority"] == 1:
        guidance = "🔴 꼭 필요한 상품 · 가격을 확인하고 구매하세요."
    elif item["priority"] == 2:
        guidance = "🟡 가격이 괜찮으면 구매 · 비싸면 보류해도 좋아요."
    else:
        guidance = "🟢 선택 구매 · 비싸면 부담 없이 건너뛰세요."
    st.caption(guidance + (f" 희망 상한: {money(item['ceiling'])}/개" if item["ceiling"] else ""))
    with st.form(f"purchase_{selected}"):
        price_col, quantity_col = st.columns(2)
        with price_col:
            unit_price = st.number_input("개당 가격 (원)", min_value=0, max_value=100000000, step=100, value=0)
        with quantity_col:
            quantity = st.number_input("수량", min_value=0.01, max_value=10000.0, value=1.0, step=1.0, format="%.2f")
        allow_high = st.checkbox("상한가를 넘어도 구매", value=False, disabled=not bool(item["ceiling"])) if item["ceiling"] else False
        bought = st.form_submit_button("🛒 이 가격·수량으로 카트에 담기", type="primary", use_container_width=True)
    if bought:
        if unit_price <= 0:
            st.warning("개당 가격을 1원 이상 입력해주세요.")
        elif item["ceiling"] and unit_price > item["ceiling"] and not allow_high:
            st.warning("희망 상한가보다 비싸요. 보류하거나 ‘상한가를 넘어도 구매’를 체크하세요.")
        else:
            amount = purchase_total(unit_price, quantity)
            cart.append({**item, "unit_price": unit_price, "quantity": quantity, "total": amount})
            st.session_state.pending = [p for p in pending if p["id"] != selected]
            st.session_state.notice = f"{item['name']} · {money(amount)} 카트에 담았어요."
            st.rerun()
    hold_col, delete_col = st.columns(2)
    with hold_col:
        if st.button("↪ 비싸서 보류", use_container_width=True):
            # Keep the memo, moving this item behind others of the same priority.
            item["id"] = st.session_state.next_id
            st.session_state.next_id += 1
            st.session_state.notice = "구매하지 않고 메모에 남겼어요. 같은 중요도의 뒤로 옮겼어요."
            st.rerun()
    with delete_col:
        with st.popover("메모 취소", use_container_width=True):
            st.caption("구매하지 않을 메모만 삭제합니다. 카트 총액에는 반영되지 않아요.")
            if st.button("구매 없이 메모 삭제", key=f"delete_{selected}"):
                st.session_state.pending = [p for p in pending if p["id"] != selected]
                st.session_state.notice = "구매하지 않은 메모를 삭제했어요."
                st.rerun()

st.caption("💡 수량은 개당 가격의 기준과 맞추세요(봉·팩·kg 등).")
with st.popover("사용 안내 · 데이터 보관"):
    st.write("상품 추가 → 중요도순 선택 → 개당 가격·수량 입력 → 카트 담기 순서로 사용하세요. 가격 입력은 카트 담기 버튼을 누를 때 반영됩니다.")
    st.write("비싸서 보류하면 메모는 남고 총액은 변하지 않습니다. 카트에서 복원하면 구매 금액이 총액에서 빠집니다. 희망 상한가는 참고 기준이며 실제 매장 가격을 조회하지 않습니다.")
    st.warning("데이터는 현재 접속 세션에만 보관됩니다. 새로고침·연결 종료·서버 재시작 시 사라질 수 있습니다. 중요한 구매 기록의 영구 보관용으로 사용하지 마세요.")
    st.caption("한 화면에서 사용하는 구성입니다. 아주 작은 화면, 큰 글꼴, 키보드 표시, 상품 추가·카트 펼침 상태에서는 스크롤이 생길 수 있습니다. 잠금화면 알림이나 푸시 알림은 제공하지 않습니다.")
