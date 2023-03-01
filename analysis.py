import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sh = {
    # 'submissionid': 'Submission ID',
    # 'respon'Respondent ID',
    'timestamp': 'Submitted at',
    'email': 'What is your email address?',
    'region': 'What region do you live in?',
    # 'Untitled short answer field (1)',
    'frequency': 'How often do you enter Howth?',
    # 'How do you usually enter Howth?',
    'car': 'How do you usually enter Howth? (Car / Motorcycle)',
    'bus': 'How do you usually enter Howth? (Bus)',
    'train': 'How do you usually enter Howth? (Train)',
    'bike': 'How do you usually enter Howth? (Bike / Scooter)',
    'walk': 'How do you usually enter Howth? (Walk)',
    # 'Why do you usually make these journeys into Howth?',
    'work': 'Why do you usually make these journeys into Howth? (Work)',
    'kids': 'Why do you usually make these journeys into Howth? (Dropping off children for school)',
    'pleasure': 'Why do you usually make these journeys into Howth? (Tourism / Pleasure)',
    'other_reason': 'Why do you usually make these journeys into Howth? (Other)',
    # 'other_reason': 'Untitled short answer field (2)',
    'congestion': 'On a scale of 1-5, how big of an issue is congestion in Howth? (5 being the most)',
    'support': 'Would you support congestion pricing (a daily fee to enter by car, only at peak hours) in Howth, which would lower traffic and delays? (only for non-residents)',
    # 'Untitled short answer field (3)',
    'price': 'If congestion pricing was implemented, what is the maximum price (€) you would pay before stopping driving to enter Howth through Sutton Cross?',
    # 'Any other comments?',
}
regions = []


def readCarData():
    files = ['thurs-m.csv', 'thurs-a.csv']
    days = []
    for fn in files:
        cars = pd.read_csv(f'data/{fn}')
        cars['time'] = pd.to_datetime(cars['time'])
        cars = cars.set_index('time')
        cars['total_count'] = cars['howth_count'] + cars['sutton_count']
        days.append(cars)
    return days


def surveyStats(survey, printStats=True):
    stats = {}

    # CONGESTION
    stats['congestion_rating'] = survey[sh['congestion']].mean().round(2)

    # REGION
    stats['region'] = survey[sh['region']].value_counts().to_dict()

    # FREQUENCY
    stats['frequency'] = survey[sh['frequency']].value_counts().to_dict()

    # ENTRY MODES
    stats['entry_modes'] = {
        'car': survey[sh['car']],
        'bus': survey[sh['bus']],
        'train': survey[sh['train']],
        'bike': survey[sh['bike']],
        'walk': survey[sh['walk']],
    }

    # REASONS
    stats['reason'] = {
        'work': survey[sh['work']],
        'kids': survey[sh['kids']],
        'pleasure': survey[sh['pleasure']],
        'other': survey[sh['other_reason']],
    }

    # SUPPORT
    stats['support'] = survey[sh['support']].value_counts().to_dict()
    # PRICE
    # sort by price by keys
    stats['price'] = survey[sh['price']]

    if printStats:
        # make survey stats red
        print('\033[91mSURVEY STATS\033[0m', '-' * 20, sep='\n')
        output = [
            {'Congestion rating': stats['congestion_rating']},
            {
                'Region': ', '.join(
                    [
                        f'{k} ({round(v / len(survey) * 100, 2)}%)'
                        for k, v in stats['region'].items()
                    ]
                )
            },
            {
                'Frequency': ', '.join(
                    [
                        f'{k} ({round(v / len(survey) * 100, 2)}%)'
                        for k, v in stats['frequency'].items()
                    ]
                )
            },
            {
                'Entry modes': ', '.join(
                    [
                        f'{k} ({round(v.mean() * 100, 2)}%)'
                        for k, v in stats['entry_modes'].items()
                    ]
                )
            },
            {
                'Reason': ', '.join(
                    [
                        f'{k} ({round(v.mean() * 100, 2)}%)'
                        for k, v in stats['reason'].items()
                    ]
                )
            },
            {
                'Support': ', '.join(
                    [
                        f'{k} ({round(v / len(survey) * 100, 2)}%)'
                        for k, v in stats['support'].items()
                    ]
                )
            },
            {'Avg Price': stats['price'].mean().round(2)},
            {
                'Price distribution': ', '.join(
                    [
                        f'{k} ({round(v / len(survey) * 100, 2)}%)'
                        for k, v in sorted(
                            stats['price'].value_counts().to_dict().items()
                        )
                    ]
                )
            },
        ]

        for o in output:
            for k, v in o.items():
                print(f'\033[92m{k}\033[0m: \033[94m{v}\033[0m')

        print('-' * 20)
    return stats


def calculateElasticity(base_demand, priceData):
    def getPercentAbovePrice(price):
        return sum([priceData[p] for p in priceData if p > price]) / total

    total = sum(priceData.values())
    prices = list(range(10))
    return prices, [base_demand * getPercentAbovePrice(p) for p in prices]


def calculateCorrelations(survey, stats, printStats=True):
    cors = {}

    noCars = np.array(list(map(lambda x: not x, survey[sh['car']])))
    carPlus = np.array(
        list(
            map(
                lambda x: x[0] and x[1],
                zip(
                    survey[sh['car']],
                    survey[sh['bus']]
                    | survey[sh['train']]
                    | survey[sh['bike']]
                    | survey[sh['walk']],
                ),
            )
        )
    )

    support = np.array(
        list(
            map(lambda x: True if x == 'Yes' else False, survey[sh['support']])
        )
    )
    frequency = np.array(
        list(
            map(
                lambda x: {
                    'Rarely or never': 1,
                    'Once a month': 2,
                    'Once a week': 3,
                    'A few times a week': 4,
                    'Every weekday': 5,
                    'Daily': 6,
                }[x],
                survey[sh['frequency']],
            )
        )
    )
    congestion = np.array(survey[sh['congestion']])

    prices = np.array(survey[sh['price']])

    cors['noCar-support'] = np.corrcoef(noCars, support)[0][1]
    cors['noCar-frequency'] = np.corrcoef(noCars, frequency)[0][1]
    cors['noCar-congestion'] = np.corrcoef(noCars, congestion)[0][1]

    cors['car+-support'] = np.corrcoef(carPlus, support)[0][1]
    cors['car+-frequency'] = np.corrcoef(carPlus, frequency)[0][1]
    cors['car+-congestion'] = np.corrcoef(carPlus, congestion)[0][1]

    cors['congestion-support'] = np.corrcoef(congestion, support)[0][1]
    cors['congestion-price'] = np.corrcoef(
        congestion[prices > 0], prices[prices > 0]
    )[0][1]

    cors['frequency-congestion'] = np.corrcoef(frequency, congestion)[0][1]
    cors['frequency-support'] = np.corrcoef(frequency, support)[0][1]
    print(regions)

    if printStats:
        print('\033[91mCORRELATIONS\033[0m', '-' * 20, sep='\n')
        output = [
            {'No car - support': cors['noCar-support'].round(2)},
            {'No car - frequency': cors['noCar-frequency'].round(2)},
            {'No car - congestion': cors['noCar-congestion'].round(2)},
            {'Car+ - support': cors['car+-support'].round(2)},
            {'Car+ - frequency': cors['car+-frequency'].round(2)},
            {'Car+ - congestion': cors['car+-congestion'].round(2)},
            {'Congestion - support': cors['congestion-support'].round(2)},
            {'Congestion - price': cors['congestion-price'].round(2)},
            {'Frequency - congestion': cors['frequency-congestion'].round(2)},
            {'Frequency - support': cors['frequency-support'].round(2)},
        ]
        for o in output:
            for k, v in o.items():
                print(f'\033[92m{k}\033[0m: \033[94m{v}\033[0m')

        print('-' * 20)


def main():
    days = readCarData()
    survey = pd.read_csv('data/init-survey.csv')

    stats = surveyStats(survey, printStats=True)
    regions = list(stats['region'].keys())

    cors = calculateCorrelations(survey, stats, printStats=True)

    exit(0)
    fig, ax = plt.subplots()

    base_demand = sum(days[0]['total_count'])

    for r in regions + ['All']:
        priceData = {
            k: v
            for k, v in survey[sh['price']][survey[sh['region']] == r]
            .value_counts()
            .to_dict()
            .items()
            if k != 0
        }
        if not priceData:
            continue

        prices, demand = calculateElasticity(base_demand, priceData)

        ax.plot(demand, prices, label=r)

    ax.set_ylabel('Price (€)')
    ax.set_xlabel('Quantity (Cars)')
    ax.set_title('Price Elasticity of Demand')

    ax.legend()
    plt.show()


if __name__ == '__main__':
    main()
