import yfinance as yf
sectors = ["^NSEI", "^NSEBANK", "^CNXIT", "^CNXAUTO", "^CNXPHARMA", "^CNXFMCG", "^CNXMETAL"]
for s in sectors:
    try:
        df = yf.download(s, period="5d", progress=False)
        print(f"{s}: {not df.empty}")
    except Exception as e:
        print(f"{s}: Error")
