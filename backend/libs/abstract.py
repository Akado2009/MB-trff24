import abc
import requests
import shutil
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractParserInterface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def parse(
        self,
        username: str,
        task_id: int,
        db_session: AsyncSession,
    ) -> None:
        # modify typing
        pass

    # download picture is the base method
    def _download_picture(self, url: str, pic_name: str) -> bool:
        try:
            res = requests.get(url, stream = True)
            if res.status_code == 200:
                with open(f"{pic_name}",'wb') as f:
                    shutil.copyfileobj(res.raw, f)
                self.logger.info('Image sucessfully Downloaded: ', pic_name)
                return True
            else:
                self.logger.error('Image Couldn\'t be retrieved')
                return False
        except:
            self.logger.error('Image Couldn\'t be retrieved')
            return False
