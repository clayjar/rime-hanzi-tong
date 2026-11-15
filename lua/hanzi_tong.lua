-- 漢字通 / Han Character Bridge
--
-- Labels candidates, hides languages the user turned off, and round-robins
-- the languages that remain so one frequency list does not fill the menu.
--
-- v0.1 does not predict from context. contextual_score() is the hook for a
-- later cross-language model over the committed sentence, including mixed
-- pronunciations. It returns nil, and the round-robin order is unchanged.
--
-- A later optional fuzzy layer may treat Japanese ん as n or ng.
-- This filter does not rewrite spellings.

local labels = {
  G = "官",
  Y = "粵",
  M = "閩",
  H = "韓",
  J = "日",
}

local disable_option = {
  G = "disable_guan",
  Y = "disable_yue",
  M = "disable_min",
  H = "disable_han",
  J = "disable_ri",
}

local language_order = { "G", "Y", "M", "H", "J" }

-- Return a quality adjustment, or nil to leave the candidate where it is.
-- committed_text is the text already sent in this session. v0.1 ignores it.
local function contextual_score(cand, committed_text)
  return nil
end

local function committed_text(context)
  if context.get_commit_text then
    local ok, text = pcall(function()
      return context:get_commit_text()
    end)
    if ok and type(text) == "string" then
      return text
    end
  end
  return ""
end

local function is_user_phrase(cand)
  local kind = cand.type or ""
  return kind == "user_phrase" or kind:find("user", 1, true) ~= nil
end

-- Spelling hints look like "Gbang1" or "Jni0 hon0".
-- Korean and Japanese use a final 0 because they have no tone.
local function annotate(comment)
  local marker, rest = comment:match("^([GYMHJ])(.*)$")
  if not marker then
    return nil, comment
  end
  if marker == "H" or marker == "J" then
    rest = rest:gsub("0", "")
  end
  rest = rest:gsub("%s+", " ")
  rest = rest:gsub("^%s+", ""):gsub("%s+$", "")
  if rest == "" then
    return marker, labels[marker]
  end
  return marker, labels[marker] .. " " .. rest
end

local function balance(input, env)
  local context = env.engine.context
  local history = committed_text(context)
  local disabled = {}
  for marker, option in pairs(disable_option) do
    disabled[marker] = context:get_option(option)
  end

  local buckets = { G = {}, Y = {}, M = {}, H = {}, J = {} }
  local pinned = {}
  local other = {}

  for cand in input:iter() do
    local adjustment = contextual_score(cand, history)
    if type(adjustment) == "number" then
      cand.quality = (cand.quality or 0) + adjustment
    end

    local marker, comment = annotate(cand.comment or "")
    if marker then
      cand.comment = comment
      if not disabled[marker] then
        if is_user_phrase(cand) then
          pinned[#pinned + 1] = cand
        else
          local bucket = buckets[marker]
          bucket[#bucket + 1] = cand
        end
      end
    else
      other[#other + 1] = cand
    end
  end

  for i = 1, #pinned do
    yield(pinned[i])
  end
  for i = 1, #other do
    yield(other[i])
  end

  local index = { G = 1, Y = 1, M = 1, H = 1, J = 1 }
  local active = {}
  for i = 1, #language_order do
    local marker = language_order[i]
    if buckets[marker][1] then
      active[#active + 1] = marker
    end
  end
  while #active > 0 do
    local next_active = {}
    for i = 1, #active do
      local marker = active[i]
      local cand = buckets[marker][index[marker]]
      if cand then
        yield(cand)
        index[marker] = index[marker] + 1
        if buckets[marker][index[marker]] then
          next_active[#next_active + 1] = marker
        end
      end
    end
    active = next_active
  end
end

return {
  balance = balance,
  -- Exposed for the unit-test mirror of the comment rewrite.
  annotate = annotate,
  contextual_score = contextual_score,
}
