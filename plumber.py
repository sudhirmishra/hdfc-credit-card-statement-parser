import pdfplumber
import csv, os, argparse

def process(input, output, password):
    pdf = pdfplumber.open(input, password=password)
    pages = pdf.pages

    total_amount=0.0
    
    indian = []
    foreign = []
    
    for page in pages:
        if page.extract_text().find("Domestic Transactions") > 0:
            print("Domestic");
            
            for (index, row) in enumerate(page.extract_table()):
                if index == 0 or row[0] == "" or row[0] == None:
                    if len(row) > 2 and row[1] in ['SUDHIR MISHRA', 'AKANSHA GUPTA', 'HIMANSHU GUPTA']:
                        card_name = row[1]
                    continue

                amount_index = len(row) - 2
                
                # print(row)

                indian.append({
                    "date": row[0].replace("null",""),
                    "description": row[1],
                    "currency": "INR",
                    "rp": row[2],
                    "forex_amount": "",
                    "forex_rate": "",
                    "amount": row[amount_index].replace("Cr",""),
                    "type": "Cr" if "Cr" in row[amount_index] else "Dr",
                    "card_name": card_name
                })
        
                total_amount += sum(float(item["amount"].replace(",","")) * (0 if item["type"] == "Cr" else 1) for item in indian)

        elif page.extract_text().find("International Transactions") > 0:
            print("Foreign")

            # Foreign transactions
            table_settings={
                "explicit_vertical_lines": [380] # Split the currency
            }
            
            for (index, row) in enumerate(page.extract_table(table_settings=table_settings)):

                if index == 0 or row[0] == "" or row[0] == None:
                    continue
                
                amount_index = len(row) - 2
                
                print(row)

                foreign.append({
                    "date": row[0].replace("null",""),
                    "description": row[1],
                    "currency": row[2][0:3],
                    "forex_amount": row[2][4:],
                    "forex_rate": '%.2f' % (float(row[amount_index].replace("Cr", "").replace(" ", "").replace(",",""))/float(row[2][4:].replace(",",""))),
                    "amount": row[amount_index].replace("Cr","").replace(" ", "").replace(",",""),
                    "type": "Cr" if "Cr" in row[amount_index] else "Dr"
                })

            # Credits in foreign statements are marked as deduction
            total_amount += sum(float(item["amount"].replace(",","")) * (-1 if item["type"] == "Cr" else 1) for item in foreign)

    print("Processed " + input + ". Total due should be " + str(total_amount))

    # Output to CSV
    combined = []
    combined.extend(indian)
    combined.extend(foreign)

    fields = ["date", "currency", "description", "rp", "forex_amount", "forex_rate", "amount", "type", "card_name"]
    with open(output, 'w') as file:
        writer = csv.DictWriter(file, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL, fieldnames=fields)
        writer.writeheader()

        for row in combined:
            writer.writerow({ key: row[key] for key in fields })


def main(args):
    for file_name in os.listdir(args.in_dir):
        root, ext = os.path.splitext(file_name)
        if ext.lower() != '.pdf':
            continue

        pdf_path = os.path.join(args.in_dir, file_name)

        out_name = root + '.csv'
        out_path = os.path.join(args.out_dir, out_name)

        print(f'Processing: {pdf_path}')
        process(pdf_path, out_path, args.password)
        print(f'Output file: {out_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-dir', type=str, required=True, help='directory to read statement PDFs from.')
    parser.add_argument('--out-dir', type=str, required=True, help='directory to store statement CSV to.')
    parser.add_argument('--password', type=str, default=None, help='password for the statement PDF.')
    args = parser.parse_args()

    main(args)