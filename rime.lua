-- 漢字通 / Han Character Bridge
-- The Weasel installer appends this hook to the user rime.lua if it is missing.
local ok, hanzi_tong = pcall(require, "hanzi_tong")
if ok then
  hanzi_tong_balance = hanzi_tong.balance
end
