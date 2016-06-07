from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Catagory, Base, CatalogItem, User

engine = create_engine('postgresql+psycopg2://catalog:catalog@localhost/catalog')
#engine = create_engine('sqlite:///catalogwithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Matt Cherry", email="mttchrry@gmail.com",
             picture='https://scontent-iad3-1.xx.fbcdn.net/hphotos-xap1'
             '/t31.0-8/886852_10153956933495127_8950105571312993824_o.jpg')
session.add(User1)
session.commit()

# Create dummy user
User2 = User(name="Rob Baristo", email="baristo@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/'
             '18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User2)
session.commit()


# Catagory for UrbanBurger
catagory1 = Catagory(user_id=User1.id, name="Football")

session.add(catagory1)
session.commit()

catalogItem2 = CatalogItem(
       user_id=User1.id,
       name="Football",
       description="An oblong leather ball",
       catagory=catagory1)

session.add(catalogItem2)
session.commit()


catalogItem1 = CatalogItem(
       user_id=1, name="Goal Post",
       description="Uprights for Feild Goals and tearing down after wins",
       catagory=catagory1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(
       user_id=1,
       name="Helmet",
       description="A false sense of security and invulnerability",
       catagory=catagory1)

session.add(catalogItem2)
session.commit()

# Catagory for Super Stir Fry
catagory2 = Catagory(user_id=2, name="Soccer")

session.add(catagory2)
session.commit()


catalogItem1 = CatalogItem(
       user_id=2,
       name="Soccer Ball",
       description="Round ball with pentagons",
       catagory=catagory2)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(
       user_id=2,
       name="Goalie Gloves",
       description="Legal cheating aperatus",
       catagory=catagory2)

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(
       user_id=1,
       name="Cleats",
       description="Spiky shoes for digging into opponents shins",
       catagory=catagory2)

session.add(catalogItem3)
session.commit()

catalogItem4 = CatalogItem(
       user_id=1,
       name="Goal ",
       description="Aim the ball here, invariably miss",
       catagory=catagory2)

session.add(catalogItem4)
session.commit()


# Catagory for Panda Garden
catagory1 = Catagory(user_id=1, name="Basketball")

session.add(catagory1)
session.commit()


catalogItem1 = CatalogItem(
       user_id=2,
       name="Jordan's",
       description="The only show worth owning, clearly",
       catagory=catagory1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(
       user_id=1,
       name="Basketball",
       description="So Bouncy and orange",
       catagory=catagory1)

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(
       user_id=1,
       name="Rim",
       description="It feels like its 10 feet tall",
       catagory=catagory1)

session.add(catalogItem3)
session.commit()


print "added catalog items!"
