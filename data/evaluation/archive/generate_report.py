from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading('DATASET RECONNAISSANCE REPORT', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('Customer Support on Twitter (twcs.csv)')
doc.add_paragraph()

# 1. FILE INFORMATION
doc.add_heading('1. FILE INFORMATION', level=1)

table = doc.add_table(rows=7, cols=2)
table.style = 'Table Grid'
data = [
    ('Property', 'Value'),
    ('File Path', r'C:\Users\DELL\Desktop\hiver\archive\twcs\twcs.csv'),
    ('Format', 'CSV (UTF-8 encoded)'),
    ('File Size', '492.6 MB'),
    ('Total Rows', '2,811,774'),
    ('Total Columns', '7'),
    ('Time Range', 'August 29, 2011 - December 3, 2017'),
]
for i, (prop, val) in enumerate(data):
    table.rows[i].cells[0].text = prop
    table.rows[i].cells[1].text = val

doc.add_paragraph()
doc.add_heading('Columns:', level=2)

table2 = doc.add_table(rows=8, cols=3)
table2.style = 'Table Grid'
cols_data = [
    ('Column', 'Data Type', 'Description'),
    ('tweet_id', 'String', 'Unique tweet identifier'),
    ('author_id', 'String', 'Username of tweet author (brand account or customer)'),
    ('inbound', 'Boolean (String)', 'True = customer message, False = brand response'),
    ('created_at', 'String', 'Twitter timestamp'),
    ('text', 'String', 'Tweet content'),
    ('response_tweet_id', 'String', 'Comma-separated IDs of tweets that reply TO this tweet'),
    ('in_response_to_tweet_id', 'String', 'ID of tweet this is replying to (empty if first in chain)'),
]
for i, row_data in enumerate(cols_data):
    for j, cell_data in enumerate(row_data):
        table2.rows[i].cells[j].text = cell_data

doc.add_paragraph()

# 2. SAMPLE DATA
doc.add_heading('2. SAMPLE DATA', level=1)
doc.add_heading('Representative Rows:', level=2)

doc.add_paragraph('Row 1: tweet_id=1, author_id=sprintcare, inbound=False, text="@115712 I understand. I would like to assist you...", response_tweet_id=2, in_response_to_tweet_id=3')
doc.add_paragraph('Row 2: tweet_id=2, author_id=115712, inbound=True, text="@sprintcare and how do you propose we do that", response_tweet_id="", in_response_to_tweet_id=1')

doc.add_heading('Column Meanings:', level=2)

table3 = doc.add_table(rows=6, cols=2)
table3.style = 'Table Grid'
col_means = [
    ('Column', 'Interpretation'),
    ('tweet_id', 'Each row = one TWEET (not a conversation)'),
    ('author_id', 'Can be a brand account (e.g., AmazonHelp) or a customer (anonymized as numeric IDs)'),
    ('inbound', 'CRITICAL field: True = customer initiating contact, False = brand reply'),
    ('text', 'The actual message content'),
    ('response_tweet_id / in_response_to_tweet_id', 'Links that connect tweets into conversations'),
]
for i, row_data in enumerate(col_means):
    for j, cell_data in enumerate(row_data):
        table3.rows[i].cells[j].text = cell_data

doc.add_paragraph()

# 3. DATASET STRUCTURE
doc.add_heading('3. DATASET STRUCTURE', level=1)
doc.add_heading('How Conversations Work:', level=2)
doc.add_paragraph('Customer (inbound=True) -> Brand (inbound=False) -> Customer -> Brand -> ...')

doc.add_heading('Reconstructing Threads:', level=2)
doc.add_paragraph('1. Start with a brand reply (inbound=False) that has in_response_to_tweet_id pointing to a customer tweet')
doc.add_paragraph('2. Follow the chain backwards using in_response_to_tweet_id')
doc.add_paragraph('3. Follow forwards using response_tweet_id to see subsequent replies')
doc.add_paragraph('4. Each row is a single tweet, NOT a conversation')

doc.add_heading('Row Granularity:', level=2)
doc.add_paragraph('Each row = 1 tweet. Conversations span multiple rows linked by in_response_to_tweet_id / response_tweet_id.')
doc.add_paragraph()

# 4. BRAND ANALYSIS
doc.add_heading('4. BRAND ANALYSIS', level=1)
doc.add_heading('Top 20 Brands by Volume:', level=2)

table4 = doc.add_table(rows=21, cols=4)
table4.style = 'Table Grid'
brands_top20 = [
    ('Rank', 'Brand', 'Tweets', '% of Total'),
    ('1', 'AmazonHelp', '169,840', '6.04%'),
    ('2', 'AppleSupport', '106,860', '3.80%'),
    ('3', 'Uber_Support', '56,270', '2.00%'),
    ('4', 'SpotifyCares', '43,265', '1.54%'),
    ('5', 'Delta', '42,253', '1.50%'),
    ('6', 'Tesco', '38,573', '1.37%'),
    ('7', 'AmericanAir', '36,764', '1.31%'),
    ('8', 'TMobileHelp', '34,317', '1.22%'),
    ('9', 'comcastcares', '33,031', '1.17%'),
    ('10', 'British_Airways', '29,361', '1.04%'),
    ('11', 'SouthwestAir', '28,977', '1.03%'),
    ('12', 'VirginTrains', '27,817', '0.99%'),
    ('13', 'Ask_Spectrum', '25,860', '0.92%'),
    ('14', 'XboxSupport', '24,557', '0.87%'),
    ('15', 'sprintcare', '22,381', '0.80%'),
    ('16', 'hulu_support', '21,872', '0.78%'),
    ('17', 'sainsburys', '19,466', '0.69%'),
    ('18', 'GWRHelp', '19,364', '0.69%'),
    ('19', 'AskPlayStation', '19,098', '0.68%'),
    ('20', 'ChipotleTweets', '18,749', '0.67%'),
]
for i, row_data in enumerate(brands_top20):
    for j, cell_data in enumerate(row_data):
        table4.rows[i].cells[j].text = cell_data

doc.add_paragraph()
doc.add_paragraph('Total unique brands: 108')
doc.add_paragraph()

# 5. TOP BRAND CANDIDATES
doc.add_heading('5. TOP BRAND CANDIDATES', level=1)
doc.add_heading('Detailed Metrics for Top 10:', level=2)

table5 = doc.add_table(rows=11, cols=7)
table5.style = 'Table Grid'
metrics = [
    ('Brand', 'Brand Tweets', 'Multi-turn Rate', 'Unique Customers', 'Est. Conversations', 'Avg Length', 'Data Quality'),
    ('AmazonHelp', '169,840', '50.2%', '71,048', '85,274', '4.0 turns', 'Good'),
    ('AppleSupport', '106,860', '29.5%', '76,365', '31,564', '2.7 turns', 'Good'),
    ('Uber_Support', '56,270', '32.0%', '38,299', '18,036', '3.0 turns', 'Good'),
    ('SpotifyCares', '43,265', '31.8%', '27,793', '13,786', '3.0 turns', 'Good'),
    ('Delta', '42,253', '28.4%', '22,330', '12,014', '2.9 turns', 'Good'),
    ('Tesco', '38,573', '28.9%', '15,594', '11,148', '3.0 turns', 'Good'),
    ('AmericanAir', '36,764', '39.6%', '21,686', '14,556', '2.9 turns', 'Good'),
    ('TMobileHelp', '34,317', '28.4%', '19,942', '9,759', '2.9 turns', 'Good'),
    ('comcastcares', '33,031', '23.0%', '21,823', '7,625', '2.8 turns', 'Good'),
    ('British_Airways', '29,361', '34.4%', '14,212', '10,099', '3.0 turns', 'Good'),
]
for i, row_data in enumerate(metrics):
    for j, cell_data in enumerate(row_data):
        table5.rows[i].cells[j].text = cell_data

doc.add_paragraph()
doc.add_heading('Key Observations:', level=2)
doc.add_paragraph('- AmazonHelp has highest volume AND highest multi-turn rate (50%)')
doc.add_paragraph('- AppleSupport has most unique customers (76K) but lower multi-turn (29%)')
doc.add_paragraph('- AmericanAir has high multi-turn rate (40%) suggesting engaged conversations')
doc.add_paragraph('- Most brands have ~28-40% multi-turn conversation rate')
doc.add_paragraph()

# 6. CONVERSATION QUALITY
doc.add_heading('6. CONVERSATION QUALITY (Top 5 Brands)', level=1)

doc.add_heading('AmazonHelp:', level=2)
doc.add_paragraph('- Customer intent diversity: High (order issues, delivery, Prime, refunds, account)')
doc.add_paragraph('- Brand response rate: Almost all customer messages get a reply')
doc.add_paragraph('- Resolution info: Brand often redirects to phone/chat/DM for complex issues')
doc.add_paragraph('- Thread types: Mix of quick resolutions (2 turns) and complex issues (6+ turns)')
doc.add_paragraph('- Data quality issues: Some non-English content, encoding artifacts in ~8% of threads')

doc.add_heading('AppleSupport:', level=2)
doc.add_paragraph('- Customer intent diversity: Medium-High (iOS issues, device problems, Apple ID)')
doc.add_paragraph('- Brand response rate: Good')
doc.add_paragraph('- Resolution info: Often asks for DM or specific details; limited in-thread resolution')
doc.add_paragraph('- Thread types: Short (70% are 2-turn), quick escalations to DM')
doc.add_paragraph('- Data quality: Clean ASCII content, but many conversations end quickly')

doc.add_heading('Delta:', level=2)
doc.add_paragraph('- Customer intent diversity: High (flight booking, cancellations, delays, rebooking, baggage)')
doc.add_paragraph('- Brand response rate: Good')
doc.add_paragraph('- Resolution info: Polite apologies, some rebooking assistance, often asks for DM with details')
doc.add_paragraph('- Thread types: 68% are 2-turn (quick responses), but meaningful conversations exist')
doc.add_paragraph('- Data quality: Good, some customers frustrated but civil')

doc.add_heading('British_Airways:', level=2)
doc.add_paragraph('- Customer intent diversity: High (booking, upgrades, cancellations, compensation)')
doc.add_paragraph('- Brand response rate: Good')
doc.add_paragraph('- Resolution info: More detailed responses, booking-specific help')
doc.add_paragraph('- Thread types: Longer threads (34% are 4+ turns), more detailed interactions')
doc.add_paragraph('- Data quality: Professional tone, good for learning formal brand voice')

doc.add_heading('AmericanAir:', level=2)
doc.add_paragraph('- Customer intent diversity: High (flights, delays, rebooking, compensation)')
doc.add_paragraph('- Brand response rate: High (39.6% multi-turn rate)')
doc.add_paragraph('- Resolution info: Detailed flight-specific help, compensation policies')
doc.add_paragraph('- Thread types: Good mix of short and long conversations')
doc.add_paragraph('- Data quality: Clean, professional')
doc.add_paragraph()

# 7. RECOMMENDATION
doc.add_heading('7. IMPORTANT RECOMMENDATION: BEST 3 BRANDS', level=1)

doc.add_heading('#1 RECOMMENDED: AmazonHelp', level=2)
doc.add_paragraph('Volume: 169,840 brand tweets (largest by far)')
doc.add_paragraph('Conversations: ~85K multi-turn conversations')
doc.add_paragraph('Intent Diversity: Extremely high (orders, delivery, Prime, refunds, account, payments, etc.)')
doc.add_paragraph('Multi-turn Rate: 50.2% (best among top brands)')
doc.add_paragraph('Avg Conversation Length: 4.0 turns (longest)')
doc.add_paragraph('')
doc.add_paragraph('Reasoning: Massive volume provides statistical robustness for intent classification. Highest multi-turn rate means more complete conversations to learn from. Diverse support issues = rich intent taxonomy. Longest average conversations provide more context for resolution patterns.')
doc.add_paragraph('')
doc.add_paragraph('Main Advantage: Data volume + conversation depth + intent diversity = best for generalizable agent')
doc.add_paragraph('')
doc.add_paragraph('Main Risk: Some encoding issues with non-English content, many conversations redirect to phone/chat')

doc.add_heading('#2 RECOMMENDED: Delta', level=2)
doc.add_paragraph('Volume: 42,253 brand tweets')
doc.add_paragraph('Conversations: ~12K multi-turn conversations')
doc.add_paragraph('Intent Diversity: High (flights, delays, cancellations, rebooking, bags)')
doc.add_paragraph('Multi-turn Rate: 28.4%')
doc.add_paragraph('Avg Conversation Length: 2.9 turns')
doc.add_paragraph('')
doc.add_paragraph('Reasoning: Well-defined domain (airline support) with clear intent categories. Structured processes (flight changes, compensation) easier to learn. Professional communication style learnable by AI. Good balance of volume and conversation quality.')
doc.add_paragraph('')
doc.add_paragraph('Main Advantage: Cleaner domain = easier intent classification + more predictable resolution patterns')
doc.add_paragraph('')
doc.add_paragraph('Main Risk: Lower multi-turn rate means fewer complete conversation examples')

doc.add_heading('#3 RECOMMENDED: British_Airways', level=2)
doc.add_paragraph('Volume: 29,361 brand tweets')
doc.add_paragraph('Conversations: ~10K multi-turn conversations')
doc.add_paragraph('Intent Diversity: High (bookings, upgrades, cancellations, compensation)')
doc.add_paragraph('Multi-turn Rate: 34.4% (good)')
doc.add_paragraph('Avg Conversation Length: 3.0 turns')
doc.add_paragraph('')
doc.add_paragraph('Reasoning: Detailed brand responses with specific booking/reference numbers. More formal tone useful for learning professional customer service. Good for learning compensation and upgrade resolution patterns.')
doc.add_paragraph('')
doc.add_paragraph('Main Advantage: More detailed resolution information in threads')
doc.add_paragraph('')
doc.add_paragraph('Main Risk: Smaller volume than top 2')
doc.add_paragraph()

# 8. EXAMPLES
doc.add_heading('8. EXAMPLE CONVERSATIONS', level=1)

doc.add_heading('AmazonHelp Examples:', level=2)

doc.add_heading('Example 1: Order Issue (Thread IDs: 618, 616, 615, 617)', level=3)
doc.add_paragraph('[CUSTOMER] 115820: @AmazonHelp 3 different people have given 3 different answers and I still do not have my order. Says Refund pending for 2 weeks')
doc.add_paragraph('[BRAND] AmazonHelp: @115820 I am sorry we have let you down! Without providing any personal information, will you describe the issue?')
doc.add_paragraph('[CUSTOMER] 115820: Way to drop the ball on customer service @115821 so pissed right now!')
doc.add_paragraph('[BRAND] AmazonHelp: @115820 We would like to take a further look into this with you! Please reach us by phone or chat here: ...')
doc.add_paragraph('Why useful: Shows escalation pattern, customer frustration, brand deflection to other channels')

doc.add_heading('Example 2: Prime Cancellation (Thread with 6 turns)', level=3)
doc.add_paragraph('[CUSTOMER] 116082: @AmazonHelp Thats the thing I told customer service. I created a new email address for the Prime trial')
doc.add_paragraph('[BRAND] AmazonHelp: Canceling your Prime membership can be done here:...')
doc.add_paragraph('[CUSTOMER] 116082: I called customer service and was told my membership would not be renewed. I was just charged.')
doc.add_paragraph('[BRAND] AmazonHelp: It would be best if you get in touch with us by phone or chat')
doc.add_paragraph('Why useful: Shows subscription cancellation intent, multiple channel confusion')
doc.add_paragraph()

doc.add_heading('Delta Examples:', level=2)
doc.add_heading('Example 1: Flight Not Offered', level=3)
doc.add_paragraph('[BRAND] Delta: My apologies. If that flight never showed up in your search, that would mean it was full.')
doc.add_paragraph('[CUSTOMER] 115882: I checked daily and flight 1403 was never offered as an option')
doc.add_paragraph('[BRAND] Delta: I am sorry. The earlier flight may not have been available at the time of your scheduled change')
doc.add_paragraph('[CUSTOMER] Delta: why was not earlier flight offered when I tried to rebook')
doc.add_paragraph('Why useful: Shows flight rebooking intent, compensation language')
doc.add_paragraph()

doc.add_heading('British_Airways Examples:', level=2)
doc.add_heading('Example 1: Upgrade Cost Inquiry', level=3)
doc.add_paragraph('[CUSTOMER] 115892: @British_Airways Sure, how much would an upgrade cost?')
doc.add_paragraph('[BRAND] British_Airways: We are unable to offer a complimentary upgrade, however we can quote an upgrade if you...')
doc.add_paragraph('[CUSTOMER] 115892: Hi @British_Airways! My flight from MAN->LHR->BWI for Nov. 3 was canceled.')
doc.add_paragraph('Why useful: Shows upgrade pricing intent, cancellation handling')
doc.add_paragraph()

# 9. DATASET SIZE / SAMPLING
doc.add_heading('9. DATASET SIZE / SAMPLING RECOMMENDATIONS', level=1)

doc.add_heading('Practical Subsample Sizes:', level=2)

table6 = doc.add_table(rows=5, cols=2)
table6.style = 'Table Grid'
sampling = [
    ('Goal', 'Recommended Sample'),
    ('Intent Discovery', '20,000-50,000 conversations (all brands)'),
    ('Agent Training', '5,000-10,000 high-quality conversations per target brand'),
    ('Golden Evaluation Set (150-250)', '500-1000 manually labeled conversations'),
    ('Quick Experiments', '1,000-2,000 conversations'),
]
for i, row_data in enumerate(sampling):
    for j, cell_data in enumerate(row_data):
        table6.rows[i].cells[j].text = cell_data

doc.add_paragraph()
doc.add_paragraph('For 3-Brand Project:')
doc.add_paragraph('- Recommended: 15,000-30,000 total conversations')
doc.add_paragraph('- Per brand: 5,000-10,000 conversations')
doc.add_paragraph('- Format: Extract full threads (pre-computed JSON/CSV with conversation context)')
doc.add_paragraph()

# 10. FINAL SUMMARY
doc.add_heading('DATASET RECONNAISSANCE SUMMARY', level=1)

doc.add_heading('Dataset format', level=2)
doc.add_paragraph('CSV (UTF-8), 492.6 MB, 2,811,774 rows')

doc.add_heading('Important columns', level=2)
doc.add_paragraph('tweet_id - unique identifier')
doc.add_paragraph('author_id - brand account or customer ID')
doc.add_paragraph('inbound - CRITICAL: True=customer, False=brand')
doc.add_paragraph('text - message content')
doc.add_paragraph('response_tweet_id / in_response_to_tweet_id - conversation links')

doc.add_heading('Number of rows', level=2)
doc.add_paragraph('Total: 2,811,774 tweets')
doc.add_paragraph('Customer tweets: 1,537,843 (54.6%)')
doc.add_paragraph('Brand tweets: 1,273,931 (45.4%)')

doc.add_heading('Number of brands', level=2)
doc.add_paragraph('108 unique brand/support accounts')

doc.add_heading('Top 10 brands by volume', level=2)
doc.add_paragraph('1. AmazonHelp (169,840)')
doc.add_paragraph('2. AppleSupport (106,860)')
doc.add_paragraph('3. Uber_Support (56,270)')
doc.add_paragraph('4. SpotifyCares (43,265)')
doc.add_paragraph('5. Delta (42,253)')
doc.add_paragraph('6. Tesco (38,573)')
doc.add_paragraph('7. AmericanAir (36,764)')
doc.add_paragraph('8. TMobileHelp (34,317)')
doc.add_paragraph('9. comcastcares (33,031)')
doc.add_paragraph('10. British_Airways (29,361)')

doc.add_heading('Best 3 candidate brands', level=2)
doc.add_paragraph('1. AmazonHelp - Highest volume, most multi-turn conversations, diverse intents')
doc.add_paragraph('2. Delta - Clean airline domain, structured processes, good quality')
doc.add_paragraph('3. British_Airways - Detailed responses, formal tone, booking-specific help')

doc.add_heading('#1 Recommended Brand', level=2)
doc.add_paragraph('AmazonHelp')

doc.add_heading('Why', level=2)
doc.add_paragraph('- Largest volume (169K tweets, 85K+ conversations)')
doc.add_paragraph('- Highest multi-turn rate (50%) = more complete learning examples')
doc.add_paragraph('- Extremely diverse support intents (orders, delivery, Prime, refunds, account issues)')
doc.add_paragraph('- Longest average conversations (4.0 turns) = more context')
doc.add_paragraph('- Best statistical foundation for intent classification and resolution learning')

doc.add_heading('Important caveats', level=2)
doc.add_paragraph('1. Many AmazonHelp conversations redirect to phone/chat - actual resolutions often happen off-platform')
doc.add_paragraph('2. Some non-English content and encoding issues - need content filtering')
doc.add_paragraph('3. ~50% of conversations are 2-turn (quick responses) - need to filter for substantive threads')
doc.add_paragraph('4. Customer anonymization means no user history across conversations')
doc.add_paragraph('5. Time period (2011-2017) may not reflect current support patterns')

# Save
output_path = r'C:\Users\DELL\Desktop\hiver\Dataset_Reconnaissance_Report.docx'
doc.save(output_path)
print(f'Report saved to: {output_path}')
